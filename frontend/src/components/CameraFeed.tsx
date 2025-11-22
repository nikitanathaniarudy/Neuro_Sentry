import React, { useRef, useEffect, useState } from "react";

const CameraFeed: React.FC = () => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const enableStream = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (err) {
        if (err instanceof Error) {
          setError(`Error accessing camera: ${err.message}`);
        } else {
          setError("Unknown error accessing camera.");
        }
        console.error("Error accessing camera:", err);
      }
    };

    enableStream();

    // Cleanup function to stop the camera when the component unmounts
    return () => {
      if (videoRef.current && videoRef.current.srcObject) {
        const stream = videoRef.current.srcObject as MediaStream;
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      {error && <div style={{ color: "red", position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -50%)" }}>{error}</div>}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted // Muted to avoid feedback loop, can be controlled by user
        style={{ width: "100%", height: "100%", objectFit: "cover", transform: "scaleX(-1)" }} // Flip horizontally for mirror effect
      />
    </div>
  );
};

export default CameraFeed;
