var acc = document.getElementsByClassName("accordion");
var ans = document.getElementsByClassName("answer");
var i;
var isAnyOpen;
var currentY;

var findTop = function(element) {
  var rec = document.getElementById(element).getBoundingClientRect();
  return rec.top + window.scrollY;
}

for (i = 0; i < acc.length; i++) {
    acc[i].onclick = function(){
        /* Toggle between adding and removing the "active" class,
        to highlight the button that controls the panel */

        /* Toggle between hiding and showing the active panel */
        var panel = this.nextElementSibling;
        if (panel.style.display === "block") {
            panel.style.display = "none";
        } else {
        panel.style.display = "block";
        }
    }
}