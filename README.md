# 2024SpringSummerResearch

Research/coding done in Spring/Summer 2024 at Osaka University, in Higo lab, under Prof. Yoshiki Higo.

To create functionally equivalent(FE) method pair dataset.

## Core Idea

The goal of this research is to support the development of improved code-clone detection systems by building a dataset of **Functionally Equivalent** C code function pairs. Two pieces of code are considered _functionally equivalent_ if they:

- Have the same function signature (parameters and return type), and
- Produce the same output for all valid inputs, regardless of differences in implementation or structure.

To verify functional equivalence, we generate unit tests for each function and perform **cross-testing**: we run the unit tests of one function on the other, and vice versa. If both functions pass each other’s tests, we classify them as functionally equivalent. This pair is then verified by human eyes and the dataset can then be used to train or evaluate code-clone detection systems.

---

## Challenges

### 1. Unit Testing in C/C++

The most significant challenge was finding a suitable unit testing tool for C/C++. After extensive searching and experimentation, I settled on [UnitTestBot](https://github.com/UnitTestBot/UTBotCpp). This process involved a steep learning curve, including setting up Docker environments, understanding the tool's limitations, and working through a variety of compatibility issues. The tool is powerful but not without its flaws.

For example, UnitTestBot has difficulty handling many outlined types of code on their docs, one that is particularily interesting are **ternary operators**. It is unable to generate test cases that exercise both branches of a ternary condition, which would limit the number of code samples we can verify, as I am sure many codes out there uses this.

### 2. Collecting Usable Code Samples

Another major hurdle was sourcing appropriate C functions. I initially created a script to clone top-ranking C repositories from GitHub and extract individual functions. However, many functions relied on **external variables**, **custom types**, **macros** or **non-standard libraries**, making them difficult or impossible to compile and test in isolation.

To address this, I filtered for **self-contained functions** —those that could compile and run with only standard library dependencies. I used Clang to determine if these functions can run and I had to write additional logic to:

- Automatically add standard `#include` statements where needed
- Exclude functions with external dependencies
- Normalize return types

Even then, issues persisted. Many functions had **complex or non-standard return types**, such as custom structs or pointers to void (`void*`). Early in the project, I didn’t fully understand the implications of `void*` usage, but after taking an Operating Systems course, I now recognize that `void*` often implies flexible data types cast dynamically—making it extremely difficult to verify true functional equivalence. As a result, I now believe that if I were to continue this project, these functions involving `void*` should be excluded entirely from the dataset.

## The contents of this Repo

**c.py**: A Clang-based function extraction tool that parses C/C++ source files to identify and isolate self-contained functions. It filters out functions that use user-defined types, call other functions from the same file, return void, or are named "main". Extracted functions are automatically organized by signature into separate directories and have standard library headers added for compilation compatibility.

**extract.py**: A directory traversal utility that applies `c.py` to all `.c` and `.cpp` files within a specified directory tree, enabling batch processing of entire codebases.

**gen_tests.sh**: An automation script that generates unit tests using UTBot's CLI for all C/C++ files in a directory. The script automatically moves files that fail compilation to a separate error directory for manual review.

**transform_test.py**: A test driver generator that converts UTBot-generated test files into executable GoogleTest drivers. The script performs several transformations: updates include statements to reference the correct method files, extracts and corrects function names within test cases, removes UTBot-specific comments and namespace declarations, and adds the necessary main function for test execution.

**cross_test.sh**: An automated cross-testing framework that evaluates functional equivalence between extracted methods. For each method, the script runs it against all other methods' test suites (excluding self-tests), compiles the combinations using GoogleTest / CMake, and reports when methods pass each other's tests as potential functionally equivalent pairs.

## Pipeline Workflow

1. Use `extract.py` with `c.py` to extract self-contained functions from source repositories
2. Run `gen_tests.sh` to generate unit tests for the extracted methods using UTBot
3. Apply `transform_test.py` to convert test files into executable drivers
4. Execute `cross_test.sh` to perform cross-testing and identify functionally equivalent method pairs

## Future Improvements

- Implement macro detection during preprocessing to include macro-based functions
- Add SQLite database storage for method metadata and cross-testing results
- Enhance functional equivalence validation to require bidirectional test passing
- Develop automated verification pipeline for identified equivalent pairs
