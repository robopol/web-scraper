#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from gui import ScraperGUI

def main():
    """Start the GUI application"""
    root = tk.Tk()
    app = ScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 