Gimbal Camera Control
======================

This is a simple python gimbal control GUI

# ViewSheen

A series of convenience functions and Gui to control viewsheen gimbal

Read more 

- [Viewsheen&Siyi.pdf](docs/Viewsheen&Siyi.pdf)
- [VS-UAP8003K.pdf](docs/VS-UAP8003K.pdf)
- [VS_UAV_Gimbal_Camera_Protocol v1.3_20220118.pdf](docs/VS_UAV_Gimbal_Camera_Protocol v1.3_20220118.pdf)

## Installation

<pre>$ pip install -e ~/PycharmProjects/gimbal_control </pre>

to uninstall
<pre>$ pip uninstall uninstall/gimbal_control </pre>

## Twisted Documentation

https://docs.twisted.org/en/stable/

## Finding function OpenCV functions by name
OpenCV can be a big, hard to navigate library, especially if you are just getting started learning computer vision and image processing. The `find_function` method allows you to quickly search function names across modules (and optionally sub-modules) to find the function you are looking for.

#### Example:
Let's find all function names that contain the text `contour`:

<pre>import imutils
imutils.find_function("contour")</pre>

#### Output:
<pre>
1. contourArea
2. drawContours
3. findContours
4. isContourConvex
</pre>

The `contourArea` function could therefore be accessed via: `cv2.contourArea`

## Translation
Translation is the shifting of an image in either the *x* or *y* direction. To translate an image in OpenCV you would need to supply the *(x, y)*-shift, denoted as *(t<sub>x</sub>, t<sub>y</sub>)* to construct the translation matrix *M*:

![Translation equation](docs/images/translation_eq.png?raw=true)