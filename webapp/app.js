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

function openPage(page){


const content =
document.getElementById("content");



if(page==="home"){


content.innerHTML = `

<div class="main-card">

<h2>🏠 Home</h2>

<p>
Welcome to UndergroundZone
</p>

</div>

`;

}




if(page==="giveaway"){


content.innerHTML = `

<div class="main-card">

<h2>🎁 Giveaway</h2>

<p>
No active giveaway loaded yet.
</p>


<button>
JOIN
</button>


</div>

`;

}




if(page==="store"){


content.innerHTML = `

<div class="main-card">

<h2>📚 Ebook Store</h2>


<div>
🟢 Starter Ebook
<br>
2 USD
<br>
<button>
BUY
</button>
</div>


<br>


<div>
🔵 Advanced Ebook
<br>
5 USD
<br>
<button>
BUY
</button>
</div>


<br>


<div>
🟣 Premium Ebook
<br>
10 USD
<br>
<button>
BUY
</button>
</div>



</div>

`;

}




if(page==="profile"){


content.innerHTML = `

<div class="main-card">

<h2>👤 Profile</h2>

<p>
Tickets:
<span id="profileTickets">
0
</span>
</p>


<p>
Level:
1
</p>


<p>
Ebooks:
0
</p>


</div>

`;

}


}
