const tg = window.Telegram.WebApp;

tg.expand();


// =========================
// USER ID
// =========================

let userId = 123456;


if (
    tg.initDataUnsafe &&
    tg.initDataUnsafe.user
) {

    userId =
    tg.initDataUnsafe.user.id;

}



// =========================
// VARIABLES
// =========================

let tickets = 0;

let gems = 0;

let level = 1;

let energy = 100;


let canMine = true;



// =========================
// ELEMENTS
// =========================

const ticketsEl =
document.getElementById("tickets");


const energyEl =
document.getElementById("energy");


const gemsEl =
document.getElementById("gems");


const levelEl =
document.getElementById("level");


const energyFill =
document.getElementById("energyFill");


const message =
document.getElementById("message");


const pickaxe =
document.getElementById("pickaxe");



// =========================
// UPDATE UI
// =========================

function updateUI(){


    ticketsEl.innerText =
    tickets;


    energyEl.innerText =
    Math.floor(energy);


    gemsEl.innerText =
    gems;


    levelEl.innerText =
    level;



    energyFill.style.width =
    energy + "%";


}



// =========================
// LOAD PLAYER
// =========================

async function loadUser(){


    try{


        const response =
        await fetch(
        `/user/${userId}`
        );



        const data =
        await response.json();



        tickets =
        data.tickets;


        gems =
        data.gems;


        level =
        data.level;


        energy =
        data.energy;



        updateUI();


    }


    catch(error){


        console.log(error);


        message.innerText =
        "⚠️ Connection error";


    }

}



// =========================
// MINING
// =========================

async function mine(){


    if(!canMine){

        message.innerText =
        "⚠️ Slow down!";

        return;

    }



    if(energy <= 0){


        message.innerText =
        "⚡ No energy";


        return;

    }



    canMine = false;



    setTimeout(()=>{


        canMine = true;


    },700);




    // kilof animation

    pickaxe.style.transform =
    "scale(0.8) rotate(-25deg)";



    setTimeout(()=>{


        pickaxe.style.transform =
        "";


    },150);





    try{


        const response =
        await fetch(

        `/mine/${userId}`,

        {

            method:"POST"

        }

        );



        const data =
        await response.json();





        message.innerText =
        data.message;



        if(
            data.energy !== undefined
        ){

            energy =
            data.energy;

        }



        if(
            data.reward > 0
        ){


            tickets += data.reward;


            showReward(
            "+1 🎟️"
            );


        }



        updateUI();



    }


    catch(error){


        console.log(error);


        message.innerText =
        "⚠️ Mining error";


    }


}




// =========================
// REWARD POPUP
// =========================

function showReward(text){


    const popup =
    document.createElement("div");



    popup.innerText =
    text;



    popup.style.position =
    "fixed";



    popup.style.left =
    "50%";



    popup.style.top =
    "45%";



    popup.style.transform =
    "translate(-50%,-50%)";



    popup.style.fontSize =
    "45px";



    popup.style.fontWeight =
    "bold";



    popup.style.zIndex =
    "9999";



    document.body.appendChild(
    popup
    );



    setTimeout(()=>{


        popup.remove();


    },1000);


}




// =========================
// EVENTS
// =========================

pickaxe.addEventListener(
"click",
mine
);



// =========================
// START
// =========================

loadUser();

function showPage(page){


document.querySelectorAll(".page")
.forEach(
p=>p.style.display="none"
);



let element =
document.getElementById(page);



if(element){

element.style.display="block";

}


}




function buyEbook(tier){


message.innerText =
"🛒 Opening payment...";


// tutaj później podpinamy Crypto Pay


console.log(
"Buying:",
tier
);


}
