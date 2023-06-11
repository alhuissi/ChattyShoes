import { proxy } from 'valtio';

const state = proxy({
  user: Date.now(),
  conversationId: Date.now()+1,
  mainColor: "#fccbb5"
});

export default state;