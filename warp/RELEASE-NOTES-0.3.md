# machine-made Warp 0.3.0

Warp now includes Roman and Italic variable fonts with weights from 300 to 700.
Each comes as TTF and WOFF2.
The six static styles remain available as TTF, OTF and WOFF2.
The fonts report version 0.300.

The inspected ladder measured a maximum interpolation difference of 0.9971 font units in each slope.
The largest raster difference from the pen drawing was 4.994 percent in each slope.
Roman used 7,448,792 bytes; Italic used 6,679,608 bytes.
Both were below the 9,437,184-byte limit.
The inspected sources had zero contour start findings.

Fontspector reported zero FAIL, FATAL and ERROR results for each inspected font.
Eight side-bearing findings were accepted: three in Roman and five in Italic.
Six concern the ellipsis: dot spacing follows the changing stem width.
Two concern Italic zcaron: its right side bearing changes by 19 units between weights 400 and 500.
These measurements come from inspecting the versioned 0.3.0 variable fonts with Fontspector 1.9.0.
The release build also checks that its source outlines match the inspected sources and runs the numerical gates again.

The archive includes an OCR report made during packaging preparation.
Its Tesseract version and measured error rates are recorded in readability.json.
SHA256SUMS lists the SHA-256 hash of every font in the archive.
