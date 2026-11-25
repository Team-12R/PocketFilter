# Run from an AMD tool shell. POCKETFILTER_HLS_STAGE: csim, synth, cosim, or ip.
set here [file dirname [file normalize [info script]]]
set build [file normalize [file join $here .. build]]
set stage csim
if {[info exists ::env(POCKETFILTER_HLS_STAGE)]} {
    set stage $::env(POCKETFILTER_HLS_STAGE)
}
if {$stage ni {csim synth cosim ip}} {
    error "POCKETFILTER_HLS_STAGE must be csim, synth, cosim, or ip"
}
set python python
if {[info exists ::env(POCKETFILTER_PYTHON)]} {
    set python $::env(POCKETFILTER_PYTHON)
}
file mkdir $build
set vectors [file join $build vectors.txt]
exec $python [file join $here generate_vectors.py] $vectors

open_project -reset [file join $build pocketfilter_hls]
set_top sdtw_kernel
add_files [file join $here sdtw.cpp]
add_files -tb [file join $here testbench.cpp]
add_files -tb $vectors
open_solution -reset solution1 -flow_target vivado
set_part {xczu3eg-sfvc784-2-e}
create_clock -period 10 -name default
csim_design
if {$stage ne "csim"} {
    csynth_design
}
if {$stage in {cosim ip}} {
    cosim_design -rtl verilog
}
if {$stage eq "ip"} {
    export_design -format ip_catalog
}
exit
