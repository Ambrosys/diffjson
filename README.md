diffjson
========

diffjson is a command line diff tool for JSON files. You can navigate to a path before comparison, ignore sub paths and even deserialize strings into json while navigating.

Using DiffJson.py the output can be varied in different ways and integrated into own scripts.

diffjson and DiffJson.py are released under the Boost Software License.

Example
=======

left.json:
```json
{
  "c": 6,
  "aa": 7,
  "y": "diff all the things!",
  "z": true,
  "removed": {
    "red": true,
    "green": false,
    "blue": false
  },
  "common": {
    "john": 4,
    "still here": true
  },
  "equal": "!!!!",
  "wasarray": [ 1, 2 ,3 ,4],
  "stillisarray": [ 1, 1, 2, 5, 3, 4, 0, 2, 3, 2, 3, 5, 9]
}
```

right.json:
```json
{
  "y": "DIFF ALL THE THINGS!",
  "c": null,
  "aa": 5,
  "b": false,
  "z": true,
  "e": {
    "john": 5,
    "mary": 6,
    "stephen": 8
  },
  "common": {
    "john": null,
    "mary": 5,
    "still here": true
  },
  "equal": "!!!!",
  "wasarray": { "test": "5" },
  "stillisarray": [ 3, 4, 0, 2, 3, 4, 6, 4, 2, 3, 5, 9]
}
```

Output of `./diffjson left.json right.json`:

(Coloring here is done by GitHub; actual coloring done by the tool is shown in [diff.svg](https://github.com/Ambrosys/diffjson/blob/master/examples/diff.svg).)
```diff
< left.json
> right.json
~ c: 6 > null
~ aa: 7 > 5
~ y: "diff all the things!" > "DIFF ALL THE THINGS!"
< removed: {"red": true, "green": false, "blue": false}
~ common.john: 4 > null
> common.mary: 5
~ wasarray: [1, 2, 3, 4] > {"test": "5"}
~ stillisarray[0]: 1 > 3
~ stillisarray[1]: 1 > 4
~ stillisarray[2]: 2 > 0
~ stillisarray[3]: 5 > 2
~ stillisarray[6]: 0 > 6
~ stillisarray[7]: 2 > 4
~ stillisarray[8]: 3 > 2
~ stillisarray[9]: 2 > 3
~ stillisarray[10]: 3 > 5
~ stillisarray[11]: 5 > 9
< stillisarray[12]: 9
> b: false
> e: {"john": 5, "mary": 6, "stephen": 8}
```

Note: Diff of arrays isn't very intelligent implemented yet.
