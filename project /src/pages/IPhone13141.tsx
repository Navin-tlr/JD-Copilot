import React from "react";
export default (props) => {
	return (
		<div className="flex flex-col bg-white">
			<div className="flex flex-col items-center self-stretch bg-white h-[844px] px-5">
				<button className="flex flex-col items-center bg-[#FCFCFC] text-left py-8 px-[45px] mt-[132px] mb-[434px] mx-[5px] gap-[19px] rounded-[3px] border-0" 
					style={{
						boxShadow: "2px 2px 14px #0000001A"
					}}
					onClick={()=>alert("Pressed!")}>
					<img
						src={"https://figma-alpha-api.s3.us-west-2.amazonaws.com/images/a7b023bf-dd3f-4ffc-99fa-3513f4d4904b"} 
						className="w-[33px] h-[31px] object-fill"
					/>
					<span className="text-[#B6B1B1] text-[9px] w-[180px]" >
						{"You can use this tool to search around 1000+ JDs available in Internal database."}
					</span>
				</button>
				<div className="flex flex-col items-start self-stretch bg-white py-[11px] mb-[31px] rounded-lg" 
					style={{
						boxShadow: "0px 0px 6px #00000040"
					}}>
					<div className="flex items-center bg-[#8C57FF] py-1.5 px-[7px] mb-[9px] ml-3 gap-[9px] rounded-sm" 
						style={{
							boxShadow: "0px 1px 4px #00000040"
						}}>
						<div className="flex flex-col shrink-0 items-center">
							<img
								src={"https://figma-alpha-api.s3.us-west-2.amazonaws.com/images/1e268a91-7ec8-4680-8b15-c21b8d97cef9"} 
								className="w-[13px] h-[13px] object-fill"
							/>
						</div>
						<span className="text-[#ECECEC] text-[10px] font-bold" >
							{"RAG"}
						</span>
					</div>
					<span className="text-[#575353] text-xs mb-0.5 ml-3.5" >
						{"Ask, search and I’ll answer...."}
					</span>
					<div className="flex justify-between items-center self-stretch mx-3.5">
						<div className="flex flex-col shrink-0 items-center py-0.5">
							<img
								src={"https://figma-alpha-api.s3.us-west-2.amazonaws.com/images/b4df3ccc-dddc-455c-9d27-bd2394e96a10"} 
								className="w-[15px] h-[15px] object-fill"
							/>
						</div>
						<img
							src={"https://figma-alpha-api.s3.us-west-2.amazonaws.com/images/02627bdc-4cac-41a4-9f98-10719bb291ce"} 
							className="w-[19px] h-[19px] my-[9px] mx-2 object-fill"
						/>
					</div>
				</div>
			</div>
		</div>
	)
}