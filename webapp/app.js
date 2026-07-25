// =========================
// TELEGRAM MINI APP
// =========================

const tg = window.Telegram.WebApp;

tg.expand();


// =========================
// USER
// =========================

let userId = null;

if (tg.initDataUnsafe && tg.initDataUnsafe.user) {

    userId = tg.initDataUnsafe.user.id;

} else {

    // test poza Telegramem

    userId = 123456;

}



// =========================
// ELEMENTS
// =========================

const ticketsText =
document.getElementById("tickets");


const energyText =
document.getElementById("energy");


const message =
document.getElementById("message");


const pickaxe =
document.getElementById("pickaxe");



// =========================
// DATA
// =========================

let tickets = 0;

let energy = 0;



// =========================
// API ADDRESS
// =========================

// jeśli Mini App i API są na tej samej domenie:

const API = "";


// jeśli będziesz miał osobny backend,
// zmienisz np:
// const API = "https://twoje-api.up.railway.app";




// =========================
// UPDATE UI
// =========================

function updateUI(){


    ticketsText.innerText =
    tickets;


    energyText.innerText =
    energy;


}




// =========================
// LOAD USER
// =========================

async function loadUser(){


    try {


        const response =
        await fetch(
            `${API}/user/${userId}`
        );


        const data =
        await response.json();



        tickets =
        data.tickets;


        energy =
        data.energy;



        updateUI();



    }

    catch(error){


        console.log(
            "API ERROR:",
            error
        );


        message.innerText =
        "⚠️ Connection error";

    }


}




// =========================
// MINING
// =========================

async function mine(){


    if(energy <= 0){


        message.innerText =
        "⚡ No energy!";


        return;

    }



    pickaxe.style.transform =
    "scale(0.85) rotate(-15deg)";



    setTimeout(()=>{


        pickaxe.style.transform =
        "";


    },150);




    try {


        const response =
        await fetch(

            `${API}/mine/${userId}`,

            {

                method:"POST"

            }

        );



        const data =
        await response.json();



        message.innerText =
        data.message;



        await loadUser();



    }


    catch(error){


        console.log(error);


        message.innerText =
        "⚠️ Server error";

    }



}



// =========================
// PICKAXE CLICK
// =========================

pickaxe.addEventListener(
    "click",
    mine
);




// =========================
// BUTTON EVENTS
// =========================

const buttons =
document.querySelectorAll(
    ".menu button"
);



buttons.forEach(
(button,index)=>{


    button.addEventListener(
        "click",
        ()=>{


            if(index === 0){

                message.innerText =
                "👤 Profile";


            }


            if(index === 1){

                message.innerText =
                "🛒 Store coming soon";


            }


            if(index === 2){

                message.innerText =
                "🎁 Giveaway";


            }


            if(index === 3){

                message.innerText =
                "🌎 Language";


            }



        }
    );


});




// =========================
// START
// =========================

loadUser();
