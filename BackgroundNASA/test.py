import os

print(os.getcwd())
# path = os.path.dirname(os.path.abspath(__file__)) to promjenio u fileu u set_wallpaper()
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

print(os.getcwd())
print(abspath)
print(dname)
print(os.listdir())