# Build and deploy the AUP-ZU3 overlay

Use a shell with matching AMD Vivado and Vitis HLS releases and Zynq UltraScale+ device support. The build target is `xczu3eg-sfvc784-2-e`. Check the 4G or 8G marking on the board and use that variant throughout the build and deployment. Use the matching prebuilt PYNQ image. The commands below assume Bash, Python 3, Git and the repository root as the working directory. [Board markings and SD image](https://github.com/Xilinx/AUP-ZU3) · [Real Digital board support](https://github.com/RealDigitalOrg/aup-zu3-bsp)

```sh
mkdir -p hardware/build
git clone https://github.com/RealDigitalOrg/aup-zu3-bsp.git hardware/build/bsp
git -C hardware/build/bsp checkout b595ecdf37c7204129517de1773b0895bcdcc2ed
cd hardware/build
export POCKETFILTER_PYTHON=python3
POCKETFILTER_HLS_STAGE=ip vitis-run --mode hls --tcl ../hls/run_hls.tcl
# Run after the HLS command exits successfully. Replace 4gb with 8gb for that board.
variant=4gb
vivado -mode batch -source ../vivado/build_overlay.tcl -tclargs "$variant" bsp/board-files bitstream
python3 ../pynq/package_overlay.py "overlay/$variant" "pocketfilter-$variant.zip"
```

The Tcl script applies the vendor processing-system and DDR preset, connects the processor's HPM0 AXI master to the kernel control port and routes both kernel masters through HP0 to DDR. PL clock 0 drives the design at a requested 100 MHz. The `validate` stage stops after address assignment and block-design validation. The `bitstream` stage also generates the wrapper, implements the design, checks setup and hold slack and stages the matching BIT and HWH under `hardware/build/overlay/<variant>/`. Reports are in `hardware/build/vivado/<variant>/`. For an independently generated HLS export, set `POCKETFILTER_IP_REPO` to its unpacked directory containing `component.xml`.

Transfer the ZIP for the physical board to a directory visible from Jupyter, unzip it and follow the [board comparison procedure](../pynq/README.md). The archive preserves the notebook’s directory layout and includes a SHA-256 manifest. Record the ZIP hash, board marking, image and operator with the executed notebook.

For Linux or WSL, `bash hardware/vivado/build_boards.sh /path/to/board-files 4gb 8gb` from the repository root runs both implementations sequentially after IP export. It stages the Vivado projects and IP on a native temporary filesystem, then saves the overlay files, timing and utilization reports, and timestamped deployment ZIPs under `hardware/build/`. Its first line prints the native project location for debugging.
