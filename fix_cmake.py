import re, os

path = 'windows/CMakeLists.txt'
content = open(path).read()
print("Before:", content[:300])
print("---")

# Replace any Visual Studio generator version
content = re.sub(r'Visual Studio \d+ \d+', 'Visual Studio 17 2022', content)

open(path, 'w').write(content)
print("After:", open(path).read()[:300])
print("DONE - CMakeLists.txt fixed!")
