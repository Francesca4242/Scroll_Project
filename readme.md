# Scroll Visualiser

Can visualize a mapping from wrapped to unwrapped scrolls defined by a torch function. 

![image](docs/demo-image.png) 

The tool that loads webp images, or high quality tiff images and displays them next to each other. It provides a UI to quickly scroll through flat or wrapped views.  Mapping the original images of the scroll to the unwrapped equivalents with new x,y,z co-ordinates which are displayed on both sides and auto synced.


* This tool supports lazy loading and cache-ing which means that it can work on datasets far larger than RAM, considering the large amount of data there is to analyse.

* It supports smaller webp images as well as the high resolution originals.

* This tool maps the scroll images to the unwrapped lines of papyrus that we have mapped and provides a visual aid to view them side by side. It maps the x,y,z co-ordinates in the wrapped scrolls to the straightened papyrus.

* The visualisation that this tool provides allows you to scroll through multiple consecutive images.

![demo video](docs/demo-video.mp4)


