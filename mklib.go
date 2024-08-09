package main

import (
	"encoding/json"
	"fmt"
	"image"
	_ "image/jpeg"
	"os"
)

type Region struct {
	Red   int `json:"red"`
	Green int `json:"green"`
	Blue  int `json:"blue"`
}

type QuadrantColors struct {
	TopLeft     Region `json:"top_left"`
	TopRight    Region `json:"top_right"`
	BottomLeft  Region `json:"bot_left"`
	BottomRight Region `json:"bot_right"`
}

type ImageData struct {
	Filename       string         `json:"filename"`
	QuadrantColors QuadrantColors `json:"quadrant_colors"`
}

func averageColors(rect image.Rectangle, img image.Image) Region {
	rSum, gSum, bSum, count := 0, 0, 0, 0
	for y := rect.Min.Y; y < rect.Max.Y; y++ {
		for x := rect.Min.X; x < rect.Max.X; x++ {
			r, g, b, _ := img.At(x, y).RGBA()
			rSum += int(r >> 8)
			gSum += int(g >> 8)
			bSum += int(b >> 8)
			count++
		}
	}
	avgR := rSum / count
	avgG := gSum / count
	avgB := bSum / count
	return Region{
		Red:   avgR,
		Green: avgG,
		Blue:  avgB,
	}
}

func main() {
	//var results []ImageData
	outputFile, err := os.Create("output.json")
	if err != nil {
		fmt.Printf("Failed to create output file: %v\n", err)
		return
	}
	defer outputFile.Close()
	encoder := json.NewEncoder(outputFile)

	for _, arg := range os.Args[1:] {
		file, err := os.Open(arg)
		if err != nil {
			fmt.Printf("Failed to open file %s: %v\n", arg, err)
			continue
		}
		defer file.Close()

		img, _, err := image.Decode(file)
		if err != nil {
			fmt.Printf("Failed to decode image %s: %v\n", arg, err)
			continue
		}

		bounds := img.Bounds()
		width, height := bounds.Max.X, bounds.Max.Y
		var imageData ImageData
		imageData.Filename = arg
		imageData.QuadrantColors.TopLeft = averageColors(image.Rect(0, 0, width/2, height/2), img)
		imageData.QuadrantColors.TopRight = averageColors(image.Rect(width/2, 0, width, height/2), img)
		imageData.QuadrantColors.BottomLeft = averageColors(image.Rect(0, height/2, width/2, height), img)
		imageData.QuadrantColors.BottomRight = averageColors(image.Rect(width/2, height/2, width, height), img)
		if err := encoder.Encode(imageData); err != nil {
			fmt.Printf("Failed to encode results: %v\n", err)
			return
		}
	}
}
