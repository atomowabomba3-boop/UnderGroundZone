const tg = window.Telegram.WebApp;


tg.expand();



let tickets = 1;

let energy = 100;



const ticketsText =
document.getElementById("tickets");


const energyText =
document.getElementById("energy");


const message =
document.getElementById("message");


const pickaxe =
document.getElementById("pickaxe");



function update(){

    ticketsText.innerText = tickets;

    energyText.innerText = energy;

}




pickaxe.onclick = function(){


    if(energy <= 0){

        message.innerText =
        "⚡ No energy left!";

        return;

    }



    energy--;



    let chance =
    Math.random();



    if(chance <= 0.01){


        tickets++;


        message.innerText =
        "💎 Lucky find! +1 🎟️";


    }

    else {


        message.innerText =
        "⛏️ Nothing found...";


    }



    update();

}



update();
