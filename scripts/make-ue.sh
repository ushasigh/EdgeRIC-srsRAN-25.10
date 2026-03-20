cd ../srsRAN_4G
rm -rf build
mkdir build
cd build
cmake ../ 
make -j$(nproc)
