import React, { useState, useEffect } from "react";
import loadingGif from "../../assets/loading.gif";
import Button from "../../components/Button";
import Image from "../../components/Image";
import user from "../../assets/user.png";
import avatar from "../../assets/avatar.png";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import { useSnapshot } from "valtio";
import state from "../../store";
import ChatImages from "../../components/ChatImages";

const WebApp = () => {
  const snap = useSnapshot(state);
  const [open, setOpen] = useState(false);
  const [images, setImages] = useState([
    "https://hips.hearstapps.com/hmg-prod/images/cushioned-shoes-15408-1632754154.jpg",
  ]);
  const [conversationStarted, setConversationStarted] = useState(false);
  const [prompt, updatePrompt] = useState(undefined);
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState(undefined);

  const detectURLs = (message) => {
    var urlRegex = /(((https?:\/\/)|(www\.))[^\s]+)/g;
    return message.match(urlRegex);
  };

  const sendPrompt = async (event) => {
    try {
      setLoading(true);
      setConversationStarted(true);
      updatePrompt(" ");

      const requestOptions = {
        method: "POST",
        mode: "cors",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          author: snap.user,
          conversationId: snap.conversationId,
          message: prompt,
        }),
      };

      const res = await fetch(
        "https://conversation-bot-public-hyrqfogasq-ew.a.run.app/",
        requestOptions
      );

      if (!res.ok) {
        throw new Error("Something went wrong");
      }

      const { message } = await res.json();
      setAnswer(message);
      detectURLs(message) && setImages(detectURLs(message));
    } catch (err) {
      console.error(err, "err");
    } finally {
      setLoading(false);
    }
  };

  const handleClickOpen = async () => {
    try {
      setLoading(true);
      // setConversationId(Date.now())

      const requestOptions = {
        method: "POST",
        mode: "cors",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          conversationId: snap.conversationId,
          user: snap.user,
        }),
      };

      const res = await fetch(
        "https://create-conversation-public-hyrqfogasq-ew.a.run.app/",
        requestOptions
      );

      if (!res.ok) {
        throw new Error("Something went wrong");
      }

      const { message } = await res.json();
      setAnswer(message);
      detectURLs(message) && setImages(detectURLs(message));
    } catch (err) {
      console.error(err, "err");
    } finally {
      setLoading(false);
    }
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  const test = () => {
    console.log("images: ", images);
  };

  useEffect(() => {
    if (prompt != null && prompt.trim() === "") {
      setAnswer(undefined);
    }
  }, [prompt]);

  return (
    <div className="h-screen">
      <div className="grid md:grid-cols-2 grid-rows-2 gap-4">
        <div className="home">
          <div className="home-content">
            <h1>Chat shoes with us.</h1>
          </div>
          <div className="mt-14">
            <h3>
              Chatting is the new search. <br />
              Ask us about styles, size or fit and <br />
              we'll help you find it.
            </h3>
          </div>
          <div className="flex flex-row mt-12 gap-6">
            <Button
              type="filled"
              title="Chat"
              handleClick={handleClickOpen}
              customStyles="w-fit px-16 py-8 font-bold text-sm"
            />
            <Button
              type="outline"
              title="Browse"
              handleClick={() => console.log("Browse")}
              customStyles="w-fit px-8 md:px-16 py-8 font-bold text-sm"
            />
          </div>
        </div>
        <div className="md:mt-32">
          <Image />
        </div>
      </div>
      <Dialog
        sx={{ backgroundColor: "rgba(0,0,0,0)", margin: "20px" }}
        open={open}
        onClose={handleClose}
      >
        <DialogContent
          sx={{ backgroundColor: "rgba(0,0,0,0)", maxWidth: "100%" }}
        >
          <div className="spotlight__wrapper">
            <input
              type="text"
              className="spotlight__input"
              placeholder={"Hi! How can I help you?"}
              disabled
              style={{
                backgroundImage: `url(${avatar})`,
              }}
            />
            <div className="spotlight__answer">
              {images && <ChatImages images={images} />}
              {loading ? (
                <p>Loading...</p>
              ) : (
                answer && (
                  <>
                    <p>{answer}</p>
                  </>
                )
              )}
            </div>
            <div
              style={{
                marginTop: "2px",
                marginBottom: "8px",
                borderTop: "1px solid rgba(108,108,108,0.3)",
              }}
            >
              <input
                type="text"
                className="spotlight__input"
                placeholder="Ask a question"
                onChange={(e) => updatePrompt(e.target.value)}
                value={prompt}
                onKeyDown={(e) => e.key === "Enter" && sendPrompt(e)}
                disabled={loading}
                style={{
                  backgroundImage: `url(${user})`,
                }}
              />
            </div>
          </div>
        </DialogContent>
        <DialogActions>
          <Button
            customStyles="w-fit px-8 md:px-8 py-3 font-bold text-sm"
            type="outline"
            title="Cancel"
            handleClick={handleClose}
          />
          <Button
            customStyles="w-fit px-8 md:px-8 py-3 font-bold text-sm"
            type="outline"
            title="Send"
            handleClick={test}
          />
        </DialogActions>
      </Dialog>
    </div>
  );
};

export default WebApp;
