import os
import sys
import shutil
import subprocess
import numpy as np
from PIL import Image

def create_mock_images():
    print("Creating mock library images...")
    os.makedirs("test_lib", exist_ok=True)
    
    # 1. Create a set of primary/secondary color images
    colors = {
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
        "yellow": (255, 255, 0),
        "magenta": (255, 0, 255),
        "cyan": (0, 255, 255),
        "white": (255, 255, 255),
        "black": (0, 0, 0),
        "gray": (128, 128, 128)
    }
    
    for name, rgb in colors.items():
        # Rectangular images to test the center cropping to square
        img = Image.new("RGB", (300, 200), rgb)
        img.save(f"test_lib/{name}.png")
        
    # 2. Create an easter egg image
    os.makedirs("test_ee", exist_ok=True)
    ee_img = Image.new("RGB", (200, 200), (255, 128, 0)) # Orange
    ee_img.save("test_ee/orange_egg.png")

    # 3. Create a target image
    # A 400x400 image divided into 4 quadrants of Red, Green, Blue, White
    print("Creating target image...")
    target = Image.new("RGB", (400, 400))
    # Red quadrant (top-left)
    target.paste(Image.new("RGB", (200, 200), (255, 0, 0)), (0, 0))
    # Green quadrant (top-right)
    target.paste(Image.new("RGB", (200, 200), (0, 255, 0)), (200, 0))
    # Blue quadrant (bottom-left)
    target.paste(Image.new("RGB", (200, 200), (0, 0, 255)), (0, 200))
    # White quadrant (bottom-right)
    target.paste(Image.new("RGB", (200, 200), (255, 255, 255)), (200, 200))
    target.save("target.png")

def cleanup():
    print("Cleaning up test files...")
    for path in ["test_lib", "test_ee", "target.png", "lib.json", "ee.json", "output.jpg", "tests/__pycache__", "pmosaic/__pycache__", "bin/__pycache__"]:
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)

def main():
    try:
        # Step 0: Ensure we are in clean state
        cleanup()
        
        # Step 1: Create test images
        create_mock_images()
        
        # Step 2: Index library using bin/mklib.py
        print("\n--- Running mklib.py on main library ---")
        cmd_mklib = [sys.executable, "bin/mklib.py", "--libfile=lib.json", "test_lib"]
        subprocess.run(cmd_mklib, check=True)
        
        print("\n--- Running mklib.py on easter eggs ---")
        cmd_ee_mklib = [sys.executable, "bin/mklib.py", "--libfile=ee.json", "test_ee"]
        subprocess.run(cmd_ee_mklib, check=True)
        
        # Verify indexing outputs
        assert os.path.exists("lib.json"), "Library JSON file was not created"
        assert os.path.exists("ee.json"), "Easter egg JSON file was not created"
        
        with open("lib.json", "r") as f:
            lines = f.readlines()
            print(f"Main library contains {len(lines)} indexed files.")
            assert len(lines) == 9, f"Expected 9 files indexed, got {len(lines)}"
            
        with open("ee.json", "r") as f:
            lines = f.readlines()
            print(f"Easter egg library contains {len(lines)} indexed files.")
            assert len(lines) == 1, f"Expected 1 file indexed, got {len(lines)}"

        # Step 3: Create photomosaic using bin/mkpic.py (2x2 grid, RGB)
        print("\n--- Running mkpic.py (2x2 RGB, tile-size 100) ---")
        cmd_mkpic = [
            sys.executable, "bin/mkpic.py",
            "--libfiles=lib.json",
            "--easter-eggs=ee.json",
            "--outfile=output.jpg",
            "--grid-model=2x2",
            "--color-model=RGB",
            "--tile-size=100",
            "target.png"
        ]
        subprocess.run(cmd_mkpic, check=True)
        
        # Verify output
        assert os.path.exists("output.jpg"), "Output mosaic image was not created"
        out_img = Image.open("output.jpg")
        print(f"Generated mosaic size: {out_img.size}")
        assert out_img.size == (400, 400), f"Expected 400x400 size, got {out_img.size}"
        
        # Step 4: Create photomosaic using Oklab and 3x3 grid
        print("\n--- Running mkpic.py (3x3 Oklab, tile-size 100, reuse-penalty 1.0) ---")
        cmd_mkpic_oklab = [
            sys.executable, "bin/mkpic.py",
            "--libfiles=lib.json",
            "--outfile=output_oklab.jpg",
            "--grid-model=3x3",
            "--color-model=Oklab",
            "--tile-size=100",
            "--reuse-penalty=1.0",
            "target.png"
        ]
        subprocess.run(cmd_mkpic_oklab, check=True)
        
        # Verify output
        assert os.path.exists("output_oklab.jpg"), "Oklab output mosaic image was not created"
        out_img_oklab = Image.open("output_oklab.jpg")
        print(f"Generated Oklab mosaic size: {out_img_oklab.size}")
        assert out_img_oklab.size == (400, 400), f"Expected 400x400 size, got {out_img_oklab.size}"
        os.remove("output_oklab.jpg")
        
        print("\n🎉 ALL TESTS PASSED SUCCESSFULLY! 🎉")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    finally:
        cleanup()

if __name__ == "__main__":
    main()
