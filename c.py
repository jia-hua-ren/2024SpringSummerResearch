import os
import clang.cindex 
from clang.cindex import Config
import sys
import shelve

# Set the path to the libclang shared library
# Update this path to match your libclang installation
clang.cindex.Config.set_library_file('/usr/local/opt/llvm/lib/libclang.dylib')

Config.library_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "native"
)

def extract_user_defined_types(node, user_defined_types):
    """
    Recursively extract user-defined types (structs, typedefs) from the AST.
    """
    if node.kind in (clang.cindex.CursorKind.STRUCT_DECL, clang.cindex.CursorKind.TYPEDEF_DECL):
        user_defined_types.add(node.spelling)
    
    for child in node.get_children():
        extract_user_defined_types(child, user_defined_types)

def extract_function_info(node):
    """
    Extract function name, return type, and parameters from the AST node.
    """
    function_name = node.spelling
    return_type = node.result_type.spelling
    param_types = [param.type.spelling for param in node.get_arguments()]
    param_list = ', '.join(param_types)
    signature = f"{return_type} {function_name}({param_list})"
    return function_name, return_type, param_types, signature

def collect_defined_functions(node, defined_functions, source_filename):
    """
    Collect all function names defined in the source file.
    """
    if node.kind == clang.cindex.CursorKind.FUNCTION_DECL and node.is_definition():
        if node.location.file and os.path.samefile(node.location.file.name, source_filename):
            defined_functions.add(node.spelling)
    for child in node.get_children():
        collect_defined_functions(child, defined_functions, source_filename)

def extract_function_body(node):
    """
    Extract the function body from a function definition node.
    Used for 
    """
    body = []
    for child in node.get_children():
        if child.kind == clang.cindex.CursorKind.COMPOUND_STMT:
            body.extend(extract_function_body(child))
        body.append(child)
    return body

def function_calls_other_defined_functions(function_node, defined_functions, source_filename):
    """
    Check if the function calls any of the defined functions, excluding self-calls.
    """
    for stmt in extract_function_body(function_node):
        #print(stmt)
        if stmt.kind == clang.cindex.CursorKind.CALL_EXPR:
            callee = stmt.referenced
            if callee:
                callee_name = callee.spelling
                callee_location = callee.location
                #print(f"In function {function_node.spelling}, found call to {callee_name} at {callee_location}")
                if callee_name in defined_functions and callee_name != function_node.spelling:
                    # Check if the call is from the same file
                    if callee_location.file and os.path.samefile(callee_location.file.name, source_filename):
                        #print(f"Function {function_node.spelling} calls another defined function {callee_name} from the same file. Skipping.")
                        return True
    return False

def uses_user_defined_types(node, user_defined_types):
    """
    Recursively check if any part of the AST node uses user-defined types.
    """
    if node.type.get_canonical().spelling in user_defined_types:
        return True
    for child in node.get_children():
        if uses_user_defined_types(child, user_defined_types):
            return True
    return False

def function_uses_user_defined_types(function_node, user_defined_types):
    """
    Check if the function uses any user-defined types in its return type or parameters,
    or within the function body.
    """
    return_type = function_node.result_type.get_canonical().spelling
    if any(udt in return_type for udt in user_defined_types):
        return True
    for param in function_node.get_arguments():
        param_type = param.type.get_canonical().spelling
        if any(udt in param_type for udt in user_defined_types):
            return True
    body = extract_function_body(function_node)
    for stmt in body:
        if uses_user_defined_types(stmt, user_defined_types):
            return True
    return False

def save_extracted_function(filename, content, signature_info):
    '''
    this method should export the extracted functions to another c/cpp file, depending on
    the original file's extension, and adds most standard headers to the file.
    '''
    cpp_headers ='''#include <any>                 // New in C++17
#include <atomic>              // New in C++11, not fully supported by UTBot
#include <chrono>              // New in C++11, enhanced in C++20
#include <functional>          // Available before C++11
#include <memory>              // Available before C++11
#include <optional>            // New in C++17
#include <scoped_allocator>    // New in C++11
#include <stdexcept>           // Available before C++11
#include <system_error>        // New in C++11
#include <tuple>               // New in C++11
#include <type_traits>         // New in C++11
#include <utility>             // Available before C++11
#include <variant>             // New in C++17
#include <exception>           // Available before C++11
#include <initializer_list>    // New in C++11
#include <limits>              // Available before C++11
#include <new>                 // Available before C++11
#include <typeinfo>            // Available before C++11
#include <array>               // New in C++11
#include <bitset>              // Available before C++11
#include <deque>               // Available before C++11
#include <forward_list>        // New in C++11
#include <list>                // Available before C++11
#include <map>                 // Available before C++11
#include <queue>               // Available before C++11
#include <set>                 // Available before C++11
#include <stack>               // Available before C++11
#include <unordered_map>       // New in C++11
#include <unordered_set>       // New in C++11
#include <vector>              // Available before C++11
#include <algorithm>           // Available before C++11
#include <iterator>            // Available before C++11
#include <numeric>             // Available before C++11
#include <locale>              // Available before C++11
#include <string>              // Available before C++11
#include <regex>               // New in C++11
#include <fstream>             // Available before C++11
#include <iomanip>             // Available before C++11
#include <ios>                 // Available before C++11
#include <iosfwd>              // Available before C++11
#include <iostream>            // Available before C++11
#include <istream>             // Available before C++11
#include <ostream>             // Available before C++11
#include <sstream>             // Available before C++11
#include <streambuf>           // Available before C++11
#include <condition_variable>  // New in C++11
#include <future>              // New in C++11
#include <mutex>               // New in C++11
#include <shared_mutex>        // New in C++14
#include <thread>              // New in C++11
#include <complex>             // Available before C++11, not fully supported by UTBot
#include <random>              // New in C++11
#include <ratio>               // New in C++11
#include <valarray>            // Available before C++11'''

    c_headers = '''#include <assert.h>	
#include <ctype.h>	
#include <errno.h>	
#include <fenv.h>
#include <float.h>
#include <inttypes.h>	
#include <iso646.h>	
#include <limits.h>	
#include <locale.h>	
#include <math.h>	
#include <setjmp.h>	
#include <signal.h>	
#include <stdalign.h>	
#include <stdarg.h>	
#include <stdatomic.h>	
#include <stdbool.h>	
#include <stddef.h>	
#include <stdint.h>	
#include <stdio.h>	
#include <stdlib.h>	
#include <stdnoreturn.h>	
#include <string.h>	
#include <tgmath.h>	
#include <threads.h>	
#include <time.h>	
#include <uchar.h>	
#include <wchar.h>	
#include <wctype.h>
'''


    ext=".cpp" if filename.endswith(".cpp") else ".c"
    with shelve.open('counter') as db:
        if signature_info in db:
            index=db[signature_info]
        else:
            index=0
            db[signature_info]=0
    name=os.path.dirname(os.path.abspath(__file__))+"/methods/"+signature_info+"/method"+str(index)+ext
    dirname=os.path.dirname(os.path.abspath(__file__))+"/methods/"+signature_info
    if not os.path.exists(dirname):
            os.makedirs(dirname)
    with open(name, "w+") as file:
        file.write("// headers are automatically added to enable compilation\n")

        if filename.endswith(".cpp"):
            file.write(cpp_headers)
        else:
            file.write(c_headers)
        file.write("//"+filename+"\n")
        file.write(content.replace("static", "").replace("inline", ""))
        with shelve.open('counter') as db:
            db[signature_info] += 1

def extract_functions(node, source_lines, source_filename, user_defined_types, defined_functions):
    """
    Recursively extract function declarations and definitions from the AST.
    """
    if node.kind == clang.cindex.CursorKind.FUNCTION_DECL:
        if node.location.file and os.path.samefile(node.location.file.name, source_filename):
            if node.spelling == "main":
                return
            if node.result_type.spelling == "void":
                return
            
            if any(child.kind == clang.cindex.CursorKind.COMPOUND_STMT for child in node.get_children()):
                #print(f"Checking function: {node.spelling}")
                if not function_calls_other_defined_functions(node, defined_functions, source_filename) and not function_uses_user_defined_types(node, user_defined_types):
                    function_name, return_type, param_types, signature = extract_function_info(node)
                    start = node.extent.start
                    end = node.extent.end
                    function_definition = '\n'.join(source_lines[start.line-1:end.line])
                    print(source_filename)
                    print(f"Function: {function_name}")
                    print(f"Signature: {signature}")
                    print(f"Return Type: {return_type}")
                    print(f"Parameters: {'-'.join(param_types)}")

                    signature_info = return_type + ">" + f"{'-'.join(param_types)}"
                    save_extracted_function(source_filename, function_definition, signature_info)
                    print("Definition:")
                    print(function_definition.replace("static", "").replace("inline", ""))
                    print("="*40)
    for child in node.get_children():
        extract_functions(child, source_lines, source_filename, user_defined_types, defined_functions)

def main(filename):
    # Read the source file lines
    with open(filename, 'r') as f:
        source_lines = f.readlines()
    
    # Initialize the Clang index
    index = clang.cindex.Index.create()
    
    # Parse the translation unit
    tu = index.parse(filename)
    
    # Identify user-defined types
    user_defined_types = set()
    extract_user_defined_types(tu.cursor, user_defined_types)
    
    # Collect all defined functions
    defined_functions = set()
    collect_defined_functions(tu.cursor, defined_functions, filename)

    #macros = set()
    #collect_defined_macros(tu.cursor, macros)
    
    #print(f"Defined functions: {defined_functions}")

    # Extract functions and their definitions from the translation unit
    extract_functions(tu.cursor, source_lines, filename, user_defined_types, defined_functions)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python extract_functions.py <source-file>")
        sys.exit(1)
    
    filename = sys.argv[1]
    main(filename)
