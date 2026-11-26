# Usage: vivado -mode batch -source build_overlay.tcl -tclargs <4gb|8gb> <board-files> ?validate|bitstream?

if {[llength $argv] < 2 || [llength $argv] > 3} {
    error "Specify 4gb or 8gb, the Real Digital board-files directory, and optionally validate or bitstream."
}
lassign $argv variant board_repo stage
if {$variant ni {4gb 8gb}} {
    error "The AUP-ZU3 board variant must be 4gb or 8gb."
}
if {$stage eq ""} {
    set stage bitstream
}
if {$stage ni {validate bitstream}} {
    error "The Vivado stage must be validate or bitstream."
}

set part xczu3eg-sfvc784-2-e
set board_part realdigital.org:aup-zu3-${variant}:part0:1.0
set board_repo [file normalize $board_repo]
set preset_dir [file join $board_repo aup-zu3-$variant 1.0]
foreach preset_file {board.xml preset.xml} {
    if {![file isfile [file join $preset_dir $preset_file]]} {
        error "Missing Real Digital board file [file join $preset_dir $preset_file]. Pass the BSP's board-files directory."
    }
}

set here [file dirname [file normalize [info script]]]
set build [file normalize [file join $here .. build]]
set ip_repo [file join $build pocketfilter_hls solution1 impl ip]
if {[info exists ::env(POCKETFILTER_IP_REPO)]} {
    set ip_repo [file normalize $::env(POCKETFILTER_IP_REPO)]
}
if {![file isfile [file join $ip_repo component.xml]]} {
    error "Missing [file join $ip_repo component.xml]. Run the HLS flow with POCKETFILTER_HLS_STAGE=ip first."
}

proc catalog_vlnv {pattern} {
    set definitions [get_ipdefs -all -quiet -filter {DESIGN_TOOL_CONTEXTS =~ *IPI*} $pattern]
    if {[llength $definitions] == 0} {
        error "IP Integrator catalog has no IP matching $pattern."
    }
    return [lindex [lsort -dictionary [get_property VLNV $definitions]] end]
}

set_param board.repoPaths [list $board_repo]
set project_dir [file join $build vivado $variant]
create_project pocketfilter $project_dir -part $part -force
if {[llength [get_board_parts -quiet $board_part]] != 1} {
    error "Vivado could not load $board_part from $board_repo."
}
set_property board_part $board_part [current_project]
set_property target_language Verilog [current_project]
set_property ip_repo_paths [list $ip_repo] [current_project]
update_ip_catalog

create_bd_design pocketfilter
set ps [create_bd_cell -type ip -vlnv [catalog_vlnv xilinx.com:ip:zynq_ultra_ps_e:*] ps]
apply_bd_automation -rule xilinx.com:bd_rule:zynq_ultra_ps_e \
    -config {apply_board_preset "1"} $ps
# Keep the DDR configuration from the selected board preset.
set_property -dict [list \
    CONFIG.PSU__USE__M_AXI_GP0 {1} \
    CONFIG.PSU__USE__M_AXI_GP1 {0} \
    CONFIG.PSU__USE__M_AXI_GP2 {0} \
    CONFIG.PSU__USE__S_AXI_GP2 {1} \
    CONFIG.PSU__CRL_APB__PL0_REF_CTRL__FREQMHZ {100}] $ps

set smartconnect [catalog_vlnv xilinx.com:ip:smartconnect:*]
set control [create_bd_cell -type ip -vlnv $smartconnect control_axi]
set_property -dict [list CONFIG.NUM_SI {1} CONFIG.NUM_MI {1}] $control
set memory [create_bd_cell -type ip -vlnv $smartconnect memory_axi]
set_property -dict [list CONFIG.NUM_SI {2} CONFIG.NUM_MI {1}] $memory
create_bd_cell -type ip -vlnv [catalog_vlnv *:*:sdtw_kernel:*] sdtw_kernel_0

connect_bd_intf_net [get_bd_intf_pins ps/M_AXI_HPM0_FPD] [get_bd_intf_pins control_axi/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins control_axi/M00_AXI] [get_bd_intf_pins sdtw_kernel_0/s_axi_control]
connect_bd_intf_net [get_bd_intf_pins sdtw_kernel_0/m_axi_input_data] [get_bd_intf_pins memory_axi/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins sdtw_kernel_0/m_axi_output_data] [get_bd_intf_pins memory_axi/S01_AXI]
connect_bd_intf_net [get_bd_intf_pins memory_axi/M00_AXI] [get_bd_intf_pins ps/S_AXI_HP0_FPD]

set reset [create_bd_cell -type ip -vlnv [catalog_vlnv xilinx.com:ip:proc_sys_reset:*] reset]
set_property CONFIG.C_EXT_RESET_HIGH {0} $reset
set constant [catalog_vlnv xilinx.com:ip:xlconstant:*]
set locked [create_bd_cell -type ip -vlnv $constant clock_locked]
set_property CONFIG.CONST_VAL {1} $locked
set inactive [create_bd_cell -type ip -vlnv $constant reset_inactive]
set_property CONFIG.CONST_VAL {0} $inactive

proc fanout {driver sinks} {
    foreach sink $sinks {
        connect_bd_net [get_bd_pins $driver] [get_bd_pins $sink]
    }
}
fanout ps/pl_clk0 {
    ps/maxihpm0_fpd_aclk ps/saxihp0_fpd_aclk
    control_axi/aclk memory_axi/aclk sdtw_kernel_0/ap_clk reset/slowest_sync_clk
}
connect_bd_net [get_bd_pins ps/pl_resetn0] [get_bd_pins reset/ext_reset_in]
connect_bd_net [get_bd_pins clock_locked/dout] [get_bd_pins reset/dcm_locked]
fanout reset_inactive/dout {reset/aux_reset_in reset/mb_debug_sys_rst}
fanout reset/peripheral_aresetn {control_axi/aresetn memory_axi/aresetn sdtw_kernel_0/ap_rst_n}

assign_bd_address
validate_bd_design
save_bd_design
puts "Validated the PocketFilter block design for $board_part (Vivado [version -short])."
if {$stage eq "validate"} {
    return
}

set bd [get_files pocketfilter.bd]
generate_target all $bd
make_wrapper -files $bd -top -import
set_property top pocketfilter_wrapper [get_filesets sources_1]
update_compile_order -fileset sources_1

set impl [get_runs impl_1]
launch_runs $impl -to_step write_bitstream
wait_on_run $impl
set status [get_property STATUS $impl]
if {![string match {write_bitstream Complete*} $status]} {
    error "Vivado implementation did not generate a bitstream: $status. See [get_property DIRECTORY $impl]."
}

open_run $impl
set timing_report [file join $project_dir timing_summary.rpt]
report_timing_summary -file $timing_report
report_utilization -file [file join $project_dir utilization.rpt]
foreach check {setup hold} {
    set path [get_timing_paths -$check -max_paths 1 -sort_by slack -no_report_unconstrained]
    if {[llength $path] == 0 || [get_property SLACK $path] < 0} {
        error "Timing check failed for $check. Inspect $timing_report before loading the overlay."
    }
}

set bit [file join [get_property DIRECTORY $impl] pocketfilter_wrapper.bit]
set hwh [file join $project_dir pocketfilter.gen sources_1 bd pocketfilter hw_handoff pocketfilter.hwh]
foreach artifact [list $bit $hwh] {
    if {![file isfile $artifact]} {
        error "Vivado did not produce $artifact."
    }
}
set overlay [file join $build overlay $variant]
file mkdir $overlay
file copy -force $bit [file join $overlay pocketfilter.bit]
file copy -force $hwh [file join $overlay pocketfilter.hwh]
puts "Wrote pocketfilter.bit and pocketfilter.hwh in $overlay for $board_part."
