import tkinter as tk
from tkinter import messagebox, filedialog
import Levenshtein


QWERTY_TO_DOT = {'D': 1, 'W': 2, 'Q': 3, 'K': 4, 'O': 5, 'P': 6}

BRAILLE_ALPHABET = {
    'A': [1],
    'B': [1, 2],
    'C': [1, 4],
    'D': [1, 4, 5],
    'E': [1, 5],
    'F': [1, 2, 4],
    'G': [1, 2, 4, 5],
    'H': [1, 2, 5],
    'I': [2, 4],
    'J': [2, 4, 5],
    'K': [1, 3],
    'L': [1, 2, 3],
    'M': [1, 3, 4],
    'N': [1, 3, 4, 5],
    'O': [1, 3, 5],
    'P': [1, 2, 3, 4],
    'Q': [1, 2, 3, 4, 5],
    'R': [1, 2, 3, 5],
    'S': [2, 3, 4],
    'T': [2, 3, 4, 5],
    'U': [1, 3, 6],
    'V': [1, 2, 3, 6],
    'W': [2, 4, 5, 6],
    'X': [1, 3, 4, 6],
    'Y': [1, 3, 4, 5, 6],
    'Z': [1, 3, 5, 6]
}

def dots_to_bits(dots):
    bits = ['0'] * 6
    for d in dots:
        bits[d - 1] = '1'
    return ''.join(bits)

BRAILLE_BITS = {letter: dots_to_bits(dots) for letter, dots in BRAILLE_ALPHABET.items()}

def parse_braille_input(key_combo_list):
    result = ''
    for keys in key_combo_list:
        dots = [QWERTY_TO_DOT[k.upper()] for k in keys if k.upper() in QWERTY_TO_DOT]
        bits = dots_to_bits(dots)
        best = min(BRAILLE_BITS, key=lambda l: Levenshtein.distance(bits, BRAILLE_BITS[l]))
        result += best
    return result

class BKTreeNode:
    def __init__(self, word):
        self.word = word
        self.children = {}

class BKTree:
    def __init__(self, dist_fn):
        self.dist_fn = dist_fn
        self.root = None

    def add(self, word):
        if self.root is None:
            self.root = BKTreeNode(word)
            return

        node = self.root
        while True:
            dist = self.dist_fn(word, node.word)
            if dist in node.children:
                node = node.children[dist]
            else:
                node.children[dist] = BKTreeNode(word)
                break

    def search(self, word, max_dist):
        if self.root is None:
            return []

        candidates = [self.root]
        found = []

        while candidates:
            node = candidates.pop()
            dist = self.dist_fn(word, node.word)
            if dist <= max_dist:
                found.append((dist, node.word))

            for d in node.children:
                if dist - max_dist <= d <= dist + max_dist:
                    candidates.append(node.children[d])

        found.sort()
        return found

DICTIONARY = []
CUSTOM_DICT_FILE = "custom_dictionary.txt"
BK_TREE = None

def load_dictionary_file():
    global DICTIONARY, BK_TREE
    filepath = filedialog.askopenfilename(
        title="Select Dictionary File",
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if filepath:
        with open(filepath, "r") as f:
            words = [line.strip().upper() for line in f if line.strip()]
        try:
            with open(CUSTOM_DICT_FILE, "r") as cf:
                custom_words = [line.strip().upper() for line in cf if line.strip()]
                words += custom_words
        except FileNotFoundError:
            pass

        DICTIONARY = list(set(words))  # Remove duplicates
        BK_TREE = BKTree(Levenshtein.distance)
        for word in DICTIONARY:
            BK_TREE.add(word)

        messagebox.showinfo("Success", f"Loaded {len(DICTIONARY)} words (BK-Tree ready)")

def process_input():
    if BK_TREE is None:
        messagebox.showerror("Error", "Please load a dictionary file first.")
        return

    raw = input_entry.get()
    try:
        combo_strings = raw.strip().split()
        key_combo_list = [set(cs.upper()) for cs in combo_strings]

        decoded = parse_braille_input(key_combo_list)

        results = BK_TREE.search(decoded, max_dist=2)
        suggestion = results[0][1] if results else "(No close match)"

        decoded_label.config(text=f"Decoded: {decoded}")
        suggestion_label.config(text=f"Suggestion: {suggestion}")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to process input: {str(e)}")

def save_correction():
    word = correct_entry.get().strip().upper()
    if word:
        with open(CUSTOM_DICT_FILE, "a") as f:
            f.write(word + "\n")
        messagebox.showinfo("Saved", f"Added '{word}' to custom dictionary.")
    else:
        messagebox.showwarning("Empty", "Please enter a word to save.")


root = tk.Tk()
root.title("Braille Autocorrect with BK-Tree & Learning")

tk.Button(root, text="Load Dictionary File", command=load_dictionary_file).pack(padx=10, pady=5)

tk.Label(root, text="Enter QWERTY Braille keys (one letter at a time, space-separated):").pack(padx=10, pady=5)

input_entry = tk.Entry(root, width=60)
input_entry.pack(padx=10, pady=5)

tk.Button(root, text="Decode & Suggest", command=process_input).pack(padx=10, pady=5)

decoded_label = tk.Label(root, text="Decoded: ")
decoded_label.pack(padx=10, pady=5)

suggestion_label = tk.Label(root, text="Suggestion: ")
suggestion_label.pack(padx=10, pady=5)

tk.Label(root, text="If suggestion is wrong, type your correct word:").pack(padx=10, pady=5)
correct_entry = tk.Entry(root, width=40)
correct_entry.pack(padx=10, pady=5)
tk.Button(root, text="Save Correction", command=save_correction).pack(padx=10, pady=5)

root.mainloop()
