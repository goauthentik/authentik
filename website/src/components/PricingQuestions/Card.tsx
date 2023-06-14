import React, { useState } from "react";

interface CardProps {
    title: string;
    body: string;
}

const Card = ({ title, body }: CardProps): JSX.Element => {
    const [isActive, setIsActive] = useState(false);

    return (
        <div>
            <div
                style={{
                    padding: "1rem",
                    marginBottom: "1rem",
                    marginTop: "1rem",
                    display: "flex",
                    flexDirection: "column",
                    cursor: "pointer",
                }}
                className="card"
                onClick={() => setIsActive((state) => !state)}
            >
                <div
                    style={{
                        display: "flex",
                        flexDirection: "row",
                    }}
                >
                    <div
                        style={{
                            marginLeft: "0.5rem",
                        }}
                    >
                        <strong>{title}</strong>
                    </div>
                </div>
                {isActive && (
                    <div
                        className="card__body"
                        dangerouslySetInnerHTML={{ __html: body }}
                    >
                        {}
                    </div>
                )}
            </div>
        </div>
    );
};

export default Card;
