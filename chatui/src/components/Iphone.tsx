import React from "react";
import "./style.css";

// MCP-exported assets (local dev server)
const vector = "http://localhost:3845/assets/9d49f9e4e3d972e5fe99de585fd9952ac6047207.svg"; // send arrow
const image = "http://localhost:3845/assets/0b2ce89b2b52f214d51d2a684c096c01c0dcb9ed.svg"; // attachment
const toolBox = "http://localhost:3845/assets/e99107f05c11f364d438e580ffc8e2defe2380e4.svg"; // deep research icon (used as placeholder)
const vector2 = "http://localhost:3845/assets/e9472ded5057bf6576eec32fd660ceff9b70d10b.svg"; // rag
const vector3 = "http://localhost:3845/assets/8e40df5e274cb8bba22508714ec5a8c3aaed2700.svg"; // whisper
const vector4 = "http://localhost:3845/assets/2f1a55905e4105254854e081ffd477309c5adfc6.svg"; // group
const vector5 = "http://localhost:3845/assets/e99107f05c11f364d438e580ffc8e2defe2380e4.svg"; // reuse

export const Iphone: React.FC = () => {
    return (
        <div className="iphone">
            <div className="CHAT-COMPONENT">
                <div className="text-wrapper">Alright genius, spit out...</div>

                <div className="SEND-ARROW">
                    <img className="vector" alt="Vector" src={vector} />

                    <img className="img" alt="Vector" src={image} />
                </div>

                <div className="ATTACHMENT-ICON">
                    <img className="vector-2" alt="Vector" src={vector5} />
                </div>
            </div>

            <img className="tool-box" alt="Tool box" src={toolBox} />

            <div className="chat-history-arrow">
                <div className="group">
                    <img className="img" alt="Vector" src={vector2} />

                    <img className="vector-3" alt="Vector" src={vector3} />

                    <img className="vector-4" alt="Vector" src={vector4} />
                </div>
            </div>
        </div>
    );
};

export default Iphone;
