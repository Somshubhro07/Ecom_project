// JavaScript for changing navigation on scroll

/*window.addEventListener('scroll', function() {
    const navbar = document.querySelectorAll('nav');
    const sections = document.querySelectorAll('section');

    let currentSection = '';

    sections.forEach(function(section) {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.clientHeight;
        if (pageYOffset >= sectionTop - sectionHeight / 3) {
            currentSection = section.getAttribute('id');
        }
    });

    const navLinks = document.querySelectorAll('nav a');
    navLinks.forEach(function(link) {
        link.classList.remove('active');
        if (link.getAttribute('href').substring(1) === currentSection) {
            link.classList.add('active');
        }
    });
});*/

document.addEventListener('DOMContentLoaded', function() {
    const navbar = document.querySelector('nav');
    const sections = document.querySelectorAll('section');
    const navLinks = document.querySelectorAll('nav a');

    // Smooth scrolling when clicking on navigation links
    navLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);
            const targetOffset = targetSection.offsetTop - navbar.clientHeight + 1; // Adjusted for navbar height
            window.scrollTo({
                top: targetOffset,
                behavior: 'smooth'
            });
        });
    });

    // Change active navigation link on scroll
    window.addEventListener('scroll', function() {
        let currentSection = '';

        sections.forEach(function(section) {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            if (pageYOffset >= sectionTop - sectionHeight / 3) {
                currentSection = section.getAttribute('id');
            }
        });

        navLinks.forEach(function(link) {
            link.classList.remove('active');
            if (link.getAttribute('href').substring(1) === currentSection) {
                link.classList.add('active');
            }
        });
    });
});


//chage mode from light to dark 
$( ".change" ).on("click", function() {
    if( $( "main" ).hasClass( "dark" )) {
        $( "main" ).removeClass( "dark" );
        $( ".change" ).text( "OFF" );
    } else {
        $( "main" ).addClass( "dark" );
        $( ".change" ).text( "ON" );
    }
});
