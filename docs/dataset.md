Getting the dataset
-------------------

Try something like this:
    for i in `seq 6000 7250`; do wget --user=putyourusernamehere --password=andyourpassword http://dl.ash2txt.org/full-scrolls/Scroll1.volpkg/volumes/20230205180739/0$i.tif; (convert 0$i.tif 0$i.webp; rm 0$i.tif) & sleep 0.5; done


This downloads a set of images, and converts them all to webp as they're downloaded (so you can fit them in less space - you can use the full res ones later)