import React, { Suspense } from "react";
import { useImage } from "react-image";

function MyImage() {
  const { src } = useImage({
    srcList: "./shoe.png",
  });

  return <img src={src} />;
}

export default function Image() {
  return (
    <Suspense>
      <MyImage />
    </Suspense>
  );
}
