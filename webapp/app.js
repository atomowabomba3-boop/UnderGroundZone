const API = "";

let userId = null;



// =========================
// TELEGRAM
// =========================


if(window.Telegram && Telegram.WebApp){

    Telegram.WebApp.ready();

    Telegram.WebApp.expand();


    let user = Telegram.WebApp.initDataUnsafe.user;


    if(user){

        userId = user.id;

    }

}



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



start();







// =========================
// USER
// =========================


async function loadUser(){


    let res = await fetch(
        API+"/user/"+userId
    );


    let data = await res.json();



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


<h2>
💰 Current Giveaway
</h2>



<div id="giveaway">

Loading...

</div>



<br>


<button onclick="openShop()">

📚 Ebook Store

</button>



<button onclick="openMyEbooks()">

📖 My ebooks

</button>



<button onclick="openProfile()">

👤 Profile

</button>



</div>


`;



loadGiveaway();


}







// =========================
// GIVEAWAY
// =========================


async function loadGiveaway(){


let res = await fetch(
API+"/giveaway"
);


let data = await res.json();



let box=document.getElementById(
"giveaway"
);



if(!data.active){


box.innerHTML=`

<p>
No active giveaway
</p>

`;

return;

}




box.innerHTML=`

<div class="card">


<h2>
💰 $${data.prize}
</h2>


<p>
👥 Participants:
${data.participants}
</p>


<p>
⏳ Ends:
${data.end}
</p>


<button onclick="joinGiveaway()">

🎁 JOIN GIVEAWAY

</button>


</div>

`;



}






async function joinGiveaway(){


let res=await fetch(

API+
"/join-giveaway/"
+
userId,

{

method:"POST"

}

);



let data=await res.json();



alert(data.message);



loadUser();


loadGiveaway();


}








// =========================
// SHOP
// =========================


async function openShop(){


let res=await fetch(
API+"/ebooks"
);


let books=await res.json();



let html=`

<div class="box">


<h2>
📚 Ebook Store
</h2>

`;



for(let id in books){


let b=books[id];



html+=`

<div class="card">


<img class="ebook-image"
src="${b.image}">


<h3>
${b.name}
</h3>


<p>
💰 ${b.price} USD
</p>


<p>
🎟️ +${b.tickets} tickets
</p>


<button onclick="buy('${id}')">

💳 BUY

</button>


</div>

`;

}



html+=`

<button onclick="openHome()">

⬅️ Back

</button>


</div>

`;



document.getElementById("content").innerHTML=html;


}








async function buy(id){


let res=await fetch(

API+
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



let data=await res.json();



alert(data.message);


loadUser();


}









// =========================
// MY EBOOKS
// =========================


async function openMyEbooks(){


let res=await fetch(

API+
"/myebooks/"
+
userId

);



let books=await res.json();



let html=`

<div class="box">

<h2>
📖 My ebooks
</h2>

`;



if(books.length===0){


html+=`

<p>
No ebooks yet
</p>

`;

}


else{


books.forEach(b=>{


html+=`

<div class="card">


<img class="ebook-image"
src="${b.image}">


<h3>
${b.name}
</h3>


<button onclick="downloadBook('${b.file}')">

⬇️ Download

</button>


</div>


`;


});


}




html+=`

<button onclick="openHome()">

⬅️ Back

</button>


</div>

`;



document.getElementById("content").innerHTML=html;


}








function downloadBook(file){


window.open(

API+
"/download/"
+
userId+
"/"+
file.replace(".pdf","")

);


}








// =========================
// PROFILE
// =========================


async function openProfile(){


let res=await fetch(

API+
"/user/"
+
userId

);



let u=await res.json();



document.getElementById("content").innerHTML=`


<div class="box">


<h2>
👤 Profile
</h2>


<p>
Username:
${u.username}
</p>


<p>
🎟️ Tickets:
${u.tickets}
</p>


<p>
⭐ Level:
${u.level}
</p>



<button onclick="openHome()">

⬅️ Back

</button>


</div>


`;



}
