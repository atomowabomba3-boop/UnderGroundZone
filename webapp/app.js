// =========================
// CONFIG
// =========================

const API = "";

let userId = null;


// =========================
// TELEGRAM MINI APP
// =========================

if(window.Telegram && Telegram.WebApp){

    Telegram.WebApp.ready();

    Telegram.WebApp.expand();


    let user = Telegram.WebApp.initDataUnsafe.user;


    if(user){

        userId = user.id;

    }

}



// TESTOWY USER JEŻELI NIE MA TELEGRAMA

if(!userId){

    userId = 123456;

}



// =========================
// START
// =========================


async function start(){


    await loadUser();


    openHome();


}




// =========================
// USER
// =========================


async function loadUser(){


    let response = await fetch(
        API + "/user/" + userId
    );


    let data = await response.json();



    document.getElementById("user").innerHTML = `

    👤 ${data.username}

    <br>

    🎟️ Tickets: ${data.tickets}

    <br>

    💎 Gems: ${data.gems}

    `;


}






// =========================
// HOME
// =========================


function openHome(){


document.getElementById("content").innerHTML = `


<div class="box">


<h1>
⛏️ UndergroundZone
</h1>


<p>
Welcome to UndergroundZone
</p>



<button onclick="openShop()">

📚 Ebook Store

</button>



<button onclick="openMyEbooks()">

📖 My ebooks

</button>



<button onclick="openGiveaways()">

🎁 Giveaways

</button>



</div>


`;


}







// =========================
// SHOP
// =========================



async function openShop(){


let response = await fetch(
API + "/ebooks"
);


let ebooks = await response.json();



let html = `


<div class="box">


<h2>
📚 Ebook Store
</h2>



`;



for(let id in ebooks){


let book = ebooks[id];



html += `


<div class="card ebook-card">


<img

src="${book.image}"

class="ebook-image"


>



<h3>
${book.name}
</h3>


<p>
💰 ${book.price} USD
</p>


<p>
🎟️ +${book.tickets} tickets
</p>



<button onclick="buy('${id}')">

💳 Buy

</button>



</div>


`;



}



html += `

<button onclick="openHome()">

⬅️ Back

</button>


</div>

`;



document.getElementById("content").innerHTML = html;



}








// =========================
// TEST BUY
// =========================


async function buy(id){



let response = await fetch(

API +
"/testbuy/"
+
userId
+
"/"
+
id,

{

method:"POST"

}

);



let data = await response.json();



alert(data.message);



loadUser();


}








// =========================
// MY EBOOKS
// =========================



async function openMyEbooks(){



let response = await fetch(

API+
"/myebooks/"
+
userId

);



let books = await response.json();



let html = `


<div class="box">


<h2>
📖 My ebooks
</h2>


`;



if(books.length === 0){


html += `

<p>
You don't own any ebooks yet.
</p>

`;



}


else{


books.forEach(book=>{


html += `


<div class="card">


<h3>
${book.name}
</h3>


<img

src="${book.image}"

class="ebook-image"


>



<button onclick="downloadBook('${book.file}')">

⬇️ Download

</button>


</div>


`;



});


}



html += `


<button onclick="openHome()">

⬅️ Back

</button>


</div>


`;



document.getElementById("content").innerHTML = html;



}






function downloadBook(file){


window.open(

API+
"/download/"
+
userId
+
"/"
+
file.replace(".pdf",""),

"_blank"

);


}







// =========================
// GIVEAWAYS PLACEHOLDER
// =========================



function openGiveaways(){


document.getElementById("content").innerHTML = `


<div class="box">


<h2>
🎁 Giveaways
</h2>


<p>
Coming soon...
</p>



<button onclick="openHome()">

⬅️ Back

</button>


</div>


`;


}







// START APP

start();
