---
type: "project-page"
project: "African Stability Index"
section: "06 Outputs and Site"
status: "built"
created: "2026-10-18"
updated: 2026-10-18
---

# Wonders Photo Viewer

> [!abstract] Goal
> Let the reader open a wonder's photographs full screen with one click, swipe through a few, and leave with one more click.

## Why it exists

The owner described exactly this interaction; photographs are what make the section a pleasure.

## Precise objectives

1. One click on a wonder opens its first photo full screen.
2. Swipe, or the arrow keys, moves through three to six photos; the next one is preloaded.
3. One more click, or Escape, closes the viewer.
4. Each photo shows its credit and licence; a file without a stated licence is never shown.
5. Photos come through the Canada atlas's `commons_media` shell, moved into athena-core.

## Inputs and outputs

- **In:** Wikimedia Commons files with their licence metadata
- **Out:** the viewer

## Where it stands

Built (athena-core #17): 164 photographs; a photo whose author is not machine-readable links to its Commons page, where it is named.
