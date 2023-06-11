import React, { Suspense } from "react";
import { useImage } from "react-image";

function MyImages({images}) {
  const { src } = useImage({
    srcList: images
  });

  return <img src={src} />;
}

export default function ChatImages({images}) {
  return (
    <Suspense>
      <MyImages className="w-fit" images={images} />
    </Suspense>
  );
}
