const tg = window.Telegram.WebApp;

tg.expand();


// =======================
// USER
// =======================

let userId = 123456;


if (
    tg.initDataUnsafe &&
    tg.initDataUnsafe.user
){

    userId =
    tg.initDataUnsafe.user.id;

}



// =======================
// API
// =======================

const API = "";



// =======================
// ELEMENTS
// =======================

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



// =======================
// DATA
// =======================

let tickets = 0;

let energy = 100;

let gems = 0;

let level = 1;




// =======================
// UPDATE SCREEN
// =======================

function updateUI(){


    ticketsEl.innerText =
    tickets;


    energyEl.innerText =
    energy;


    gemsEl.innerText =
    gems;


    levelEl.innerText =
    level;



    let percent =
    energy;



    energyFill.style.width =
    percent + "%";


}



// =======================
// LOAD USER
// =======================

async function loadUser(){


try{


const res =
await fetch(
`${API}/user/${userId}`
);



const data =
await res.json();



tickets =
data.tickets;


energy =
data.energy;


gems =
data.gems;


level =
data.level;



updateUI();



}
catch(e){


console.log(e);


message.innerText =
"⚠️ Server error";


}


}




// =======================
// MINING
// =======================

async function mine(){


if(energy <= 0){


message.innerText =
"⚡ No energy!";


return;


}




// animation

pickaxe.style.transform =
"scale(.8) rotate(-20deg)";


setTimeout(()=>{


pickaxe.style.transform =
"";


},150);





try{


const res =
await fetch(

`${API}/mine/${userId}`,

{

method:"POST"

}

);



const data =
await res.json();



message.innerText =
data.message;



if(data.reward > 0){


showReward(
"+1 🎟️"
);


}



await loadUser();



}
catch(e){


console.log(e);


}



}




// =======================
// REWARD POPUP
// =======================

function showReward(text){


const popup =
document.createElement("div");


popup.innerText =
text;


popup.style.position =
"fixed";


popup.style.top =
"45%";


popup.style.left =
"50%";


popup.style.transform =
"translate(-50%,-50%)";


popup.style.fontSize =
"40px";


popup.style.zIndex =
"999";


document.body.appendChild(
popup
);



setTimeout(()=>{


popup.remove();


},1000);



}



// =======================
// CLICK
// =======================

pickaxe.addEventListener(
"click",
mine
);




// =======================
// START
// =======================

loadUser();
