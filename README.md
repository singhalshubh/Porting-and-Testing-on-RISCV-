# Porting and Testing on RISCV 

1) Echronos has been ported by using the hello.c program in generic folder. Echronos has been ported successfully (for the first time on RISCV).</br>
Porting of eChronos RTOS on RISC-V Architecture : </br>
eChronos is a formally verified Real Time Operating System (RTOS) designed for embedded micro-controllers. eChronos was targeted for tightly constrained devices without memory management units. Currently, eChronos is available on proprietary designs like ARM, PowerPC and Intel architectures. eChronos is adopted in safety critical systems like aircraft control system and medical implant devices. eChronos is one of the very few system software's not been ported to RISC-V. RISC-V is an open-source Instruction Set Architecture (ISA) that enables new era of processor development. Many standard Operating Systems, software tool chain have migrated to the RISC-V architecture. According to the latest trends, RISC-V is replacing many proprietary chips. As a secure RTOS, it is attractive to port on an open-source ISA. SHAKTI and PicoRV32 are some of the proven open-source RISC-V designs available. Now having a secure RTOS on an open-source hardware design, designed based on an open-source ISA makes it more interesting. In addition to this, the current architectures supported by eChronos are all proprietary designs and porting eChronos to the RISC-V architecture increases the secure system development as a whole. This paper, presents an idea of porting eChronos on a chip which is open-source and effective, thus reducing the cost of embedded systems. Designing a open-source system that is completely open-source reduces the overall cost, increased the security and can be critically reviewed. This paper explores the design and architecture aspect involved in porting eChronos to RISC-V. The authors have successfully ported eChronos to RISC-V architecture and verified it on spike. The port of RISC-V to eChronos is made available open-source by authors. Along with that, the safe removal of architectural dependencies and subsequent changes in eChronos are also analyzed.</br>
</br>
Results : </br>
Running the system dump of hello.c file gave an output : "Hello World" assuming the starting address of execution
of program was 10000 on the architecture. RISC-V emulator has been designed in such a way that the address
for the program needs to be specified above 10000 only. But its just a design issue which will not be of any
problem in the real chip SHAKTI. This indicates that the executable file produced by eChronos successfully
ran on spike(RISC-V emulator). The output of sample program on eChronos is available (open source).
Additions of any critical programs will be just a further extension of ported Hello World program provided
the RISC-V supports that functionality of the program. Supposedly, a program which needs to determine the
shortest path needs to be ported on RISC-V using eChronos. Program would consist of the same logic but instead
of using gcc functions we will be using generic functions as seen with print in debug.h. This ensures a safe
porting technique with no dependency on outer(alien) packages. Thus, eChronos is ported for RISC-V, for the
base program hello world. Any additions to eChronos will be an extended version of the ported hello.c file with
some extra headers files(declaring some predefined functions).
</br> </br>
eChronos real-time operating system is ported to the RISC-V architecture and successfully executed on spike.
The sample program hello.c has only one external dependency i.e. print. This is the base level porting for RISC-V
that can be used as a reference for further adaptability of complex programs. Extensive porting of libraries in
eChronos can be done by modifying the files in the same way as the sample program file.

For detailed anaylsis of how the porting was carried out, please see the paper https://arxiv.org/abs/1908.11648 accepted in **Springer LNCS Germany 2019**</br>

2) Pthread library on RISCV was tested by using testP program which is a lock based algorithm.
3) .dts link with proxykernel for compilation of user defined drivers.
4) ncurses library and zephyr-rtos were installed and tested for understanding RTOS.
