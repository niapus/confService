let currentMode = "text";

function setMode(mode) {
    currentMode = mode;
    document.getElementById("mode").value = mode;
}

function wrapSelection(wrapper) {
    const textarea = document.getElementById("editor");
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;

    const selected = textarea.value.substring(start, end);

    const before = textarea.value.substring(0, start);
    const after = textarea.value.substring(end);

    textarea.value = before + wrapper + selected + wrapper + after;

    textarea.focus();
}

function makeList(prefix) {
    const textarea = document.getElementById("editor");
    const lines = textarea.value.split("\n");

    textarea.value = lines.map(line => {
        if (line.trim() !== "") {
            return prefix + line;
        }
        return line;
    }).join("\n");
}

function indent() {
   const textarea = document.getElementById("editor");
   const lines = textarea.value.split("\n");

   textarea.value = lines.map(line => "    " + line).join("\n");
}

function outdent() {
   const textarea = document.getElementById("editor");
   const lines = textarea.value.split("\n");

   textarea.value = lines.map(line => {
      if (line.startsWith("    ")) {
         return line.substring(4);
      }
      return line;
   }).join("\n");
}
