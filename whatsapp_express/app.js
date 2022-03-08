const qrcode = require("qrcode-terminal");
const { Client } = require("whatsapp-web.js");
const fs = require("fs");
const express = require("express");
const bodyParser = require("body-parser");
const cors = require("cors");

const app = express();
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());
app.use(
  cors({
    origin: ["https://whatsappsend.aliasgeorge.tech"],
    optionsSuccessStatus: 200,
  })
);

const port = process.env.PORT || 3000;
const group_id_test = process.env.GROUP_ID_Test;
const group_id_a_batch = process.env.GROUP_ID_A_BATCH;
const group_id_ece_reminders = process.env.GROUP_ID_ECE_REMINDERS;
const secret = process.env.SECRET;

var messageOptions = {
  origin: "https://whatsappsend.aliasgeorge.tech",
  methods: "POST",
  preflightContinue: false,
  optionsSuccessStatus: 204,
};

app.post("/message", cors(messageOptions), function (req, res) {
  if (req.body.secret === secret) {
    subject = req.body.subject;
    attlink = req.body.attlink;
    classlink = req.body.classlink;
    group = req.body.group;
    pass = req.body.pass;
    if (
      (classlink === "" || classlink === null) &&
      (attlink != "" || attlink != null)
    ) {
      msg = `❗️❗️❗️\n\n_Guys mark attendance for ${subject} class_\n\n*Attendance link*: \n${attlink}`;
    } else if (
      (classlink != "" || classlink != null) &&
      (attlink === "" || attlink === null)
    ) {
      msg = `❗️❗️❗️\n\n_Guys join the ${subject} class_\n\n*Class link* : \n${classlink}\n\n${
        pass != "" ? "*Password*: " + pass.trim().split(" ")[1] : ""
      }`;
    } else {
      msg = `❗️❗️❗️\n\n_Guys mark attendance and join the ${subject} class_\n\n*Attendance link*: \n${attlink}\n\n\n*Class link*: \n${classlink} \n\n${
        pass != "" ? "*Password*: " + pass.trim().split(" ")[1] : ""
      }`;
    }

    Message(msg, group);
    res.send("Success");
  } else {
    res.send("Not Permitted");
  }
});

app.post("/birthday", cors(messageOptions), function (req, res) {
  if (req.body.secret === secret) {
    text = req.body.text;
    Message(text, "abatch");
    res.send("Success");
  } else {
    res.send("Not Permitted");
  }
});

app.listen(port, function () {
  console.log(`Server started listening to the port ${port}`);
});

async function Message(msg, group) {
  try {
    if (group === "abatch") await client.sendMessage(group_id_a_batch, msg);
    else if (group === "ecereminders" && msg != null)
      await client.sendMessage(group_id_ece_reminders, msg);
    else await client.sendMessage(group_id_test, msg);
    await timer(200);
  } catch (err) {
    console.log(err);
  }
}

// Path where the session data will be stored
const SESSION_FILE_PATH = "./session.json";

// Load the session data if it has been previously saved
let sessionCfg;
if (fs.existsSync(SESSION_FILE_PATH)) {
  sessionCfg = require(SESSION_FILE_PATH);
}

// Use the saved values
// const client = new Client({
//   puppeteer: { headless: false },
//   session: sessionCfg,
// });

const client = new Client({
  puppeteer: {
    browserWSEndpoint: `ws://localhost:3000`,
  },
  session: sessionCfg,
});

// Save session values to the file upon successful auth
client.on("authenticated", (session) => {
  console.log("youre in");
  sessionData = session;
  fs.writeFile(SESSION_FILE_PATH, JSON.stringify(session), (err) => {
    if (err) {
      console.error(err);
    }
  });
});

client.on("qr", (qr) => {
  qrcode.generate(qr, { small: true });
});

client.on("ready", async () => {
  console.log("Client is ready!");
});

client.on("message", async (msg) => {
  if (msg.body == "hello" || msg.body == "Hello") {
    await client.sendMessage(msg.from, `Hello how are you`);
    await timer(200);
  }
});

const timer = (ms) => new Promise((res) => setTimeout(res, ms));

client.on("message_create", async (msg) => {
  if (msg.to === "91xxxxxxxxxx@c.us") {
    if (msg.body === "!stop") {
      exit(0);
    }
  }
});

client.initialize();
