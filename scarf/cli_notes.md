
Different cli packages:

- Click
    - https://github.com/pallets/click
- PyInquirer
    - https://github.com/CITGuru/PyInquirer
- Cement
    - https://builtoncement.com/

Pros/cons:

- Click
    - tried it out a little bit, seems a bit unnecessarily complex for what it's supposed to do. Maybe clears up after a bit more use
    - maintained
- PyInquirer
    - currently not actively maintained, looking for a maintainer
    - some old dependencies (e. g. prompt-toolkit==1.0.1), which currently is installable (with some acrobatics), but might prove a problem later on
    - easy to make interactive, e. g. make checklists or ask questions ("Do you want to specify number of dimensions to use for PCA? (Default: 20)")
- Cement
    - might be more straightforward than click? Not a real good sense of that yet, more a feeling while going through the docs
    - can format output w/ jinja
    - can also make interactive, but not as fancy as w/ PyInquirer
