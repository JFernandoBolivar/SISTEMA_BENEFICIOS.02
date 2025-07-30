let buttons = document.querySelectorAll('#Button');

buttons.forEach(button => {
  button.addEventListener('mouseover', function() {
    this.classList.remove('btn-info');
    this.classList.add('btn-primary');
  });

  button.addEventListener('mouseout', function() {
    this.classList.remove('btn-primary');
    this.classList.add('btn-info');
  });


});


document.querySelectorAll('#redirect-icon').forEach(element => {
  element.addEventListener('click', function() {
      window.location.href = "../../index.html";
  });
});

document.querySelectorAll('.col').forEach(item => {
  item.addEventListener('click', function() {
      var flechaDiv = document.getElementById('cuadro-con-flecha');
      flechaDiv.style.opacity = '0';  // Cambiar la opacidad para hacerlo desaparecer lentamente
  });
});
