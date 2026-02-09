// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {ERC721URIStorage} from "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title TaxReceiptNFT
 * @dev NFT-based tax receipts for charitable donations
 * 
 * Features:
 * - Each donation gets a unique NFT receipt
 * - Metadata stored on IPFS (immutable proof)
 * - Verifiable by tax authorities
 * - Transferable (optional: can make soulbound)
 * - Links donation ID to token ID
 * 
 * Deployed on: Polygon (low gas fees), Base, or Arbitrum
 */
contract TaxReceiptNFT is ERC721, ERC721URIStorage, Ownable {
    uint256 private _nextTokenId;
    
    // Mapping from donation ID to token ID (one receipt per donation)
    mapping(uint256 => uint256) public donationToToken;
    
    // Mapping from token ID to donation ID
    mapping(uint256 => uint256) public tokenToDonation;
    
    // Mapping to track if a token is soulbound (non-transferable)
    mapping(uint256 => bool) public isSoulbound;
    
    // Events
    event ReceiptMinted(
        address indexed donor,
        uint256 indexed tokenId,
        uint256 indexed donationId,
        string tokenURI,
        uint256 timestamp
    );
    
    event ReceiptBurned(
        uint256 indexed tokenId,
        uint256 indexed donationId,
        uint256 timestamp
    );
    
    constructor() ERC721("TrustVoice Tax Receipt", "TVTR") Ownable(msg.sender) {
        // Start token IDs at 1 (0 is reserved for checking existence)
        _nextTokenId = 1;
    }
    
    /**
     * @dev Mint a new tax receipt NFT
     * @param donor Address to receive the receipt
     * @param donationId Database ID of the donation
     * @param uri IPFS URI with receipt metadata (ipfs://QmXxxx...)
     * @return tokenId The ID of the minted token
     */
    function mintReceipt(
        address donor,
        uint256 donationId,
        string memory uri
    ) public onlyOwner returns (uint256) {
        require(donor != address(0), "Cannot mint to zero address");
        require(donationToToken[donationId] == 0, "Receipt already minted for this donation");
        require(bytes(uri).length > 0, "Token URI cannot be empty");
        
        uint256 tokenId = _nextTokenId++;
        
        _safeMint(donor, tokenId);
        _setTokenURI(tokenId, uri);
        
        donationToToken[donationId] = tokenId;
        tokenToDonation[tokenId] = donationId;
        
        emit ReceiptMinted(donor, tokenId, donationId, uri, block.timestamp);
        
        return tokenId;
    }
    
    /**
     * @dev Mint a soulbound (non-transferable) receipt
     * @param donor Address to receive the receipt
     * @param donationId Database ID of the donation
     * @param uri IPFS URI with receipt metadata
     * @return tokenId The ID of the minted token
     */
    function mintSoulboundReceipt(
        address donor,
        uint256 donationId,
        string memory uri
    ) public onlyOwner returns (uint256) {
        uint256 tokenId = mintReceipt(donor, donationId, uri);
        isSoulbound[tokenId] = true;
        return tokenId;
    }
    
    /**
     * @dev Batch mint receipts (gas optimization)
     * @param donors Array of donor addresses
     * @param donationIds Array of donation IDs
     * @param tokenURIs Array of token URIs
     */
    function batchMintReceipts(
        address[] memory donors,
        uint256[] memory donationIds,
        string[] memory tokenURIs
    ) public onlyOwner {
        require(
            donors.length == donationIds.length && donors.length == tokenURIs.length,
            "Array lengths must match"
        );
        
        for (uint256 i = 0; i < donors.length; i++) {
            if (donationToToken[donationIds[i]] == 0) {
                mintReceipt(donors[i], donationIds[i], tokenURIs[i]);
            }
        }
    }
    
    /**
     * @dev Get token ID for a specific donation
     * @param donationId Database ID of the donation
     * @return tokenId The token ID, or 0 if no receipt exists
     */
    function getReceiptByDonation(uint256 donationId) public view returns (uint256) {
        return donationToToken[donationId];
    }
    
    /**
     * @dev Check if a receipt exists for a donation
     * @param donationId Database ID of the donation
     * @return bool True if receipt exists
     */
    function receiptExists(uint256 donationId) public view returns (bool) {
        return donationToToken[donationId] != 0;
    }
    
    /**
     * @dev Get donation ID for a token
     * @param tokenId The NFT token ID
     * @return donationId The database donation ID
     */
    function getDonationByToken(uint256 tokenId) public view returns (uint256) {
        require(_ownerOf(tokenId) != address(0), "Token does not exist");
        return tokenToDonation[tokenId];
    }
    
    /**
     * @dev Burn a receipt (in case of refund or fraud)
     * @param tokenId The token ID to burn
     */
    function burnReceipt(uint256 tokenId) public onlyOwner {
        require(_ownerOf(tokenId) != address(0), "Token does not exist");
        
        uint256 donationId = tokenToDonation[tokenId];
        
        delete donationToToken[donationId];
        delete tokenToDonation[tokenId];
        delete isSoulbound[tokenId];
        
        _burn(tokenId);
        
        emit ReceiptBurned(tokenId, donationId, block.timestamp);
    }
    
    /**
     * @dev Update token URI (in case metadata needs correction)
     * @param tokenId The token ID to update
     * @param newURI The new IPFS URI
     */
    function updateTokenURI(uint256 tokenId, string memory newURI) public onlyOwner {
        _requireOwned(tokenId);
        _setTokenURI(tokenId, newURI);
    }
    
    /**
     * @dev Override transfer to enforce soulbound tokens
     */
    function _update(address to, uint256 tokenId, address auth)
        internal
        override
        returns (address)
    {
        address from = _ownerOf(tokenId);
        
        // Allow minting (from == address(0)) and burning (to == address(0))
        // Block transfers for soulbound tokens
        if (from != address(0) && to != address(0) && isSoulbound[tokenId]) {
            revert("This receipt is soulbound and cannot be transferred");
        }
        
        return super._update(to, tokenId, auth);
    }
    
    /**
     * @dev Get total number of receipts minted
     */
    function totalSupply() public view returns (uint256) {
        return _nextTokenId - 1;
    }
    
    // Required overrides
    function tokenURI(uint256 tokenId)
        public
        view
        override(ERC721, ERC721URIStorage)
        returns (string memory)
    {
        return super.tokenURI(tokenId);
    }
    
    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721, ERC721URIStorage)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}
