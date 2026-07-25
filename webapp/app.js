let userId = null;



function getTelegramUser(){

    if(window.Telegram && Telegram.WebApp){

        Telegram.WebApp.ready();


        let user =
        Telegram.WebApp.initDataUnsafe.user;


        if(user){

            userId = user.id;

            console.log(
                "Telegram user:",
                userId
            );

        }

    }


    // test poza Telegramem

    if(!userId){

        userId = 123456;

    }

}



getTelegramUser();


const tickets = document.getElementById("tickets");
const energy = document.getElementById("energy");
const message = document.getElementById("message");
const mineButton = document.getElementById("mine");


// pobranie danych użytkownika

async function loadUser(){


    await fetch(
        `/register/${userId}`,
        {
            method:"POST"
        }
    );


    let response = await fetch(
        `/user/${userId}`
    );


    let data = await response.json();


    document.getElementById("username").innerText =
    "👤 " + data.username;


    tickets.innerText =
    data.tickets;


    energy.innerText =
    data.energy;


}




// KOPANIE

mineButton.onclick = async function(){


    mineButton.style.transform =
    "scale(0.8)";


    setTimeout(()=>{

        mineButton.style.transform =
        "scale(1)";

    },100);



    try{


        let response = await fetch(
            `/mine/${userId}`,
            {
                method:"POST"
            }
        );


        let data = await response.json();


        message.innerText =
        data.message;



        loadUser();


    }
    catch(e){

        message.innerText =
        "❌ Server error";

    }


}




// sklep

function showShop(){


    document.getElementById("panel").innerHTML = `

    <div class="card">

    <h2>📚 Ebook Shop</h2>

    <p>Coming soon...</p>

    </div>

    `;

}




// język

function showLanguage(){


    document.getElementById("panel").innerHTML = `

    <div class="card">

    <h2>🌍 Language</h2>


    <button onclick="changeLanguage('en')">
    🇬🇧 English
    </button>


    <button onclick="changeLanguage('pl')">
    🇵🇱 Polski
    </button>


    <button onclick="changeLanguage('de')">
    🇩🇪 Deutsch
    </button>


    </div>

    `;


}




async function changeLanguage(lang){


    await fetch(
        `/language/${userId}/${lang}`,
        {
            method:"POST"
        }
    );


    message.innerText =
    "🌍 Language changed";


}




// profil

function showProfile(){


    document.getElementById("panel").innerHTML = `

    <div class="card">

    <h2>👤 Profile</h2>

    <p>
    Level: 1
    </p>


    <p>
    Mining rank: Beginner
    </p>


    </div>

    `;


}



loadUser();
