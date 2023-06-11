import React from 'react'
import { useSnapshot } from 'valtio'

import state from '../store'

const Button = ({ type, title, customStyles, handleClick }) => {
  const snap = useSnapshot(state);

  const generateStyle = (type) => {
    if(type === 'filled') {
      return {
        backgroundColor: snap.mainColor,
        color: 'black'
      }
    } else if(type === "outline") {
      return {
        borderWidth: '1px',
        borderColor: 'black',
        color: 'black'
      }
    }
  }

  return (
    <button
      className={`flex-1 rounded-xl hover:opacity-60 transition ease-in-out duration-300 ${customStyles}`}
      style={generateStyle(type)}
      onClick={handleClick}
    >
      {title}
    </button>
  )
}

export default Button