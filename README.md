#Content Aware Image Resizing Application with Seam Carving Approach 

## Overview
This application uses the seam carving approach for content aware image resizing. It uses OpenCV and numpy for image processing and PyQt5 for graphical user interface. After opening the program, the user can load an image to resize it in both dimension (Height and Width). This application provides three different way to choose the target dimension for output image: Slider in percentage, spin box in percentage and spin box in pixel that make the application more user-friendly and comfort to use. After running seam carving the resized image is ready to be saved in a selected directory.

## Features
- User friendly GUI
- Easy to load the image from local folders
- Selecting the target dimension in percentage and pixel for both Height and Width
- Capable to expand and shrink the image
- Easy to save the image in local folders

## Requirements
To run this application, you'll need Python 3.10.10 installed along with the following libraries:

Name: opencv-python
Version: 4.12.0.88

Name: numpy
Version: 2.2.6

Name: PyQt5
Version: 5.15.11

## Running the Application

1. Install the required dependencies.
2. Run the application (main.py)

This will open a GUI window where you can load an image, specify the percentage or pixels to remove or add, and run seam carving.





