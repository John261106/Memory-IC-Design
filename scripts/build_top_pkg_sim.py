# Python script to build and verify spice/Top_package_test.spi
import subprocess
import os

top_pkg_scale90 = r"D:\Projects\Memory-IC-Design\spice\Top_package_scale90.spi"
with open(top_pkg_scale90, "r") as f:
    spi_text = f.read()

print("Original scale90 spi length:", len(spi_text))
