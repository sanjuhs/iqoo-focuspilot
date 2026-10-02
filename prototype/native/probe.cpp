#include "core.h"
#include <fstream>
#include <iostream>
#include <sstream>
static std::string read(const char * path){std::ifstream file(path);if(!file)throw std::runtime_error("Could not read input file");std::ostringstream out;out<<file.rdbuf();return out.str();}
int main(int argc,char ** argv) {
    try {if(argc!=5)throw std::runtime_error("Usage: focuspilot_probe model.gguf prompt.txt grammar.gbnf capture(0|1)");
        LocalModel model(argv[1],1024,4);
        std::cout<<model.generate(read(argv[2]),read(argv[3]),128,std::string(argv[4])=="1")<<'\n';
        return 0;}catch(const std::exception & error){std::cerr<<error.what()<<'\n';return 1;}
}
