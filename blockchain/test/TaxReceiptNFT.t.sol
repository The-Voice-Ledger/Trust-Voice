// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test} from "forge-std/Test.sol";
import {TaxReceiptNFT} from "../src/TaxReceiptNFT.sol";

contract TaxReceiptNFTTest is Test {
    TaxReceiptNFT public taxReceipt;
    address public owner;
    address public donor1;
    address public donor2;
    
    function setUp() public {
        owner = address(this);
        donor1 = makeAddr("donor1");
        donor2 = makeAddr("donor2");
        
        taxReceipt = new TaxReceiptNFT();
    }
    
    function testMintReceipt() public {
        uint256 donationId = 12345;
        string memory tokenURI = "ipfs://QmTest123";
        
        uint256 tokenId = taxReceipt.mintReceipt(donor1, donationId, tokenURI);
        
        assertEq(taxReceipt.ownerOf(tokenId), donor1);
        assertEq(taxReceipt.tokenURI(tokenId), tokenURI);
        assertEq(taxReceipt.getReceiptByDonation(donationId), tokenId);
        assertEq(taxReceipt.getDonationByToken(tokenId), donationId);
    }
    
    function testCannotMintDuplicateReceipt() public {
        uint256 donationId = 12345;
        string memory tokenURI = "ipfs://QmTest123";
        
        taxReceipt.mintReceipt(donor1, donationId, tokenURI);
        
        vm.expectRevert("Receipt already minted for this donation");
        taxReceipt.mintReceipt(donor1, donationId, tokenURI);
    }
    
    function testOnlyOwnerCanMint() public {
        uint256 donationId = 12345;
        string memory tokenURI = "ipfs://QmTest123";
        
        vm.prank(donor1);
        vm.expectRevert();
        taxReceipt.mintReceipt(donor2, donationId, tokenURI);
    }
    
    function testBatchMint() public {
        address[] memory donors = new address[](3);
        donors[0] = donor1;
        donors[1] = donor2;
        donors[2] = makeAddr("donor3");
        
        uint256[] memory donationIds = new uint256[](3);
        donationIds[0] = 1;
        donationIds[1] = 2;
        donationIds[2] = 3;
        
        string[] memory tokenURIs = new string[](3);
        tokenURIs[0] = "ipfs://QmTest1";
        tokenURIs[1] = "ipfs://QmTest2";
        tokenURIs[2] = "ipfs://QmTest3";
        
        taxReceipt.batchMintReceipts(donors, donationIds, tokenURIs);
        
        assertEq(taxReceipt.ownerOf(1), donor1);
        assertEq(taxReceipt.ownerOf(2), donor2);
        assertEq(taxReceipt.ownerOf(3), donors[2]);
    }
    
    function testSoulboundReceipt() public {
        uint256 donationId = 12345;
        string memory tokenURI = "ipfs://QmTest123";
        
        uint256 tokenId = taxReceipt.mintSoulboundReceipt(donor1, donationId, tokenURI);
        
        assertTrue(taxReceipt.isSoulbound(tokenId));
        
        vm.prank(donor1);
        vm.expectRevert("This receipt is soulbound and cannot be transferred");
        taxReceipt.transferFrom(donor1, donor2, tokenId);
    }
    
    function testBurnReceipt() public {
        uint256 donationId = 12345;
        string memory tokenURI = "ipfs://QmTest123";
        
        uint256 tokenId = taxReceipt.mintReceipt(donor1, donationId, tokenURI);
        
        taxReceipt.burnReceipt(tokenId);
        
        assertFalse(taxReceipt.receiptExists(donationId));
        
        vm.expectRevert();
        taxReceipt.ownerOf(tokenId);
    }
    
    function testUpdateTokenURI() public {
        uint256 donationId = 12345;
        string memory tokenURI = "ipfs://QmTest123";
        string memory newTokenURI = "ipfs://QmUpdated456";
        
        uint256 tokenId = taxReceipt.mintReceipt(donor1, donationId, tokenURI);
        
        taxReceipt.updateTokenURI(tokenId, newTokenURI);
        
        assertEq(taxReceipt.tokenURI(tokenId), newTokenURI);
    }
    
    function testTotalSupply() public {
        assertEq(taxReceipt.totalSupply(), 0);
        
        taxReceipt.mintReceipt(donor1, 1, "ipfs://QmTest1");
        assertEq(taxReceipt.totalSupply(), 1);
        
        taxReceipt.mintReceipt(donor2, 2, "ipfs://QmTest2");
        assertEq(taxReceipt.totalSupply(), 2);
    }
    
    function testReceiptExists() public {
        uint256 donationId = 12345;
        
        assertFalse(taxReceipt.receiptExists(donationId));
        
        taxReceipt.mintReceipt(donor1, donationId, "ipfs://QmTest123");
        
        assertTrue(taxReceipt.receiptExists(donationId));
    }
}
