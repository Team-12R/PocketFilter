# Run from an AMD tool shell. POCKETFILTER_HLS_STAGE: csim, synth, cosim, or ip.
set here [file dirname [file normalize [info script]]]
set build [file normalize [file join $here .. build]]
if {[info exists ::env(POCKETFILTER_BUILD)]} {
    set build [file normalize $::env(POCKETFILTER_BUILD)]
}
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
if {[info exists ::env(POCKETFILTER_HLS_VECTORS)]} {
    file copy -force [file normalize $::env(POCKETFILTER_HLS_VECTORS)] $vectors
} else {
    exec $python [file join $here generate_vectors.py] $vectors
}

# The classic project writer resolves design files relative to the project
# parent in 2024.2. Open the project from its parent for portable paths.
cd $build
open_project -reset pocketfilter_hls
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
if {$stage eq "ip"} {
    export_design -format ip_catalog
}
if {$stage in {cosim ip}} {
    cosim_design -rtl verilog
}
exit
