// wrap in the jquery function so this script is only run
// once the webpage has loaded
$(function(){

$("#thisp").text("loaded");

$('#butt').click(function() {
    console.log("clicked");
    webui.call("click", {word: "hello"});//, opts)
})

webui.actions.hello = function(args) {
    console.log("got " + args.text);
}


});
