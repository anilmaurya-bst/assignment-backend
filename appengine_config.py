from google.appengine.ext import vendor
import os
# Add any libraries install in the "ui_lib" folder.
#and adding ui_lib folder which having all compatible python library in vendor
vendor.add('lib')
#vendor.add("/Users/anilkumarmaurya/node_modules")
# vendor.add(os.path.join(os.path.dirname(os.path.realpath(__file__)), ))