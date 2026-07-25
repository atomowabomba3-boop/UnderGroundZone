const tg = window.Telegram.WebApp;


tg.ready();

tg.expand();



let userId = null;



if(tg.initDataUnsafe.user){

userId = tg.initDataUnsafe.user.id;

}
else{

userId = 1;

}




async function loadUser(){


let response = await fetch(
"/user/"+userId
);


let data = await response.json();



document.getElementById(
"username"
).innerHTML=data.username;



document.getElementById(
"tickets"
).innerHTML=data.tickets;



document.getElementById(
"gems"
).innerHTML=data.gems;


}



function home(){

document.getElementById("content").innerHTML=`

<div class="box">

<h2>🏠 Dashboard</h2>

<p>Your underground account</p>


<button onclick="openMining()">
⛏️ Mining
</button>


<button onclick="openShop()">
📚 Ebook Store
</button>


<button onclick="openGiveaway()">
🎁 Giveaway
</button>


</div>

`;

}




function openMining(){


document.getElementById("content").innerHTML=`

<div class="box">

<h2>⛏️ Mining</h2>


<p>
Find rare tickets underground.
</p>


<button onclick="mine()">
⛏️ Dig
</button>


</div>

`;

}




async function mine(){


let r = await fetch(

"/mine/"+userId,

{
method:"POST"
}

);


let data = await r.json();


alert(data.message);


loadUser();


}




function openShop(){


document.getElementById("content").innerHTML=`

<div class="box">


<h2>📚 Ebook Store</h2>


<p>Coming soon...</p>


<button>

📘 Buy Starter Ebook

</button>


<button>

🔥 Buy Premium Ebook

</button>



</div>


`;

}




function openGiveaway(){


document.getElementById("content").innerHTML=`

<div class="box">


<h2>🎁 Giveaway</h2>


<p>
No active giveaways yet.
</p>



<button>

Join

</button>


</div>

`;

}




function profile(){


document.getElementById("content").innerHTML=`

<div class="box">

<h2>👤 Profile</h2>


<p>
Language: English 🌐
</p>


<button>
Change language
</button>


</div>

`;

}



loadUser();
