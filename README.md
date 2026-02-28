# Arty Z7-20 Audio Beamforming
FPGA-based audio beamforming system targeting the Digilent Arty Z7-20 (Zynq-7020). Captures audio from I2S microphones and streams sample data to the Zynq PS via AXI DMA for beamforming processing.

## Recreating the Vivado Project

```bash
cd <repo_root>
mkdir vivado && cd vivado
vivado -mode batch -source ../recreate.tcl -tclargs --origin_dir ..
```

## Notes
- Vivado 2024.2
