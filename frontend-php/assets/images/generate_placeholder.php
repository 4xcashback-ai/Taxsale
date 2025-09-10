<?php
// Create a simple placeholder image
$width = 300;
$height = 200;

// Create image
$image = imagecreate($width, $height);

// Colors
$bg_color = imagecolorallocate($image, 102, 126, 234); // Primary color
$text_color = imagecolorallocate($image, 255, 255, 255); // White

// Fill background
imagefill($image, 0, 0, $bg_color);

// Add text
$text = "Property Location";
$font_size = 3;
$text_width = imagefontwidth($font_size) * strlen($text);
$text_height = imagefontheight($font_size);

$x = ($width - $text_width) / 2;
$y = ($height - $text_height) / 2;

imagestring($image, $font_size, $x, $y, $text, $text_color);

// Save image
imagepng($image, 'property-placeholder.png');
imagedestroy($image);

echo "Placeholder image created successfully!";
?>